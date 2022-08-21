#!/usr/bin/env python

import argparse
import json
import random
import sys
import traceback

from jinja2 import Template
from custom_script_engine import CustomScriptEngine

from py_bpmn_engine.bpmn.serializer.workflow import BpmnWorkflowSerializer
from py_bpmn_engine.bpmn.specs.events.event_types import CatchingEvent
from py_bpmn_engine.bpmn.specs.events.event_types import ThrowingEvent
from py_bpmn_engine.bpmn.specs.ManualTask import ManualTask
from py_bpmn_engine.bpmn.specs.ScriptTask import ScriptTask
from py_bpmn_engine.bpmn.workflow import BpmnWorkflow
from py_bpmn_engine.camunda.parser.CamundaParser import CamundaParser
from py_bpmn_engine.camunda.serializer.task_spec_converters import ServiceTaskConverter
from py_bpmn_engine.camunda.serializer.task_spec_converters import UserTaskConverter
from py_bpmn_engine.camunda.specs.ServiceTask import ServiceTask
from py_bpmn_engine.camunda.specs.UserTask import EnumFormField
from py_bpmn_engine.camunda.specs.UserTask import UserTask
from py_bpmn_engine.dmn.parser.BpmnDmnParser import BpmnDmnParser
from py_bpmn_engine.dmn.serializer.task_spec_converters import BusinessRuleTaskConverter
from py_bpmn_engine.dmn.specs.BusinessRuleTask import BusinessRuleTask
from py_bpmn_engine.task import Task, TaskState
from py_bpmn_engine.workflow import Workflow

wf_spec_converter = BpmnWorkflowSerializer.configure_workflow_spec_converter([ UserTaskConverter, BusinessRuleTaskConverter, ServiceTaskConverter ])
serializer = BpmnWorkflowSerializer(wf_spec_converter)

class Parser(BpmnDmnParser):

    OVERRIDE_PARSER_CLASSES = BpmnDmnParser.OVERRIDE_PARSER_CLASSES
    OVERRIDE_PARSER_CLASSES.update(CamundaParser.OVERRIDE_PARSER_CLASSES)

def parse(process, bpmn_files, dmn_files):
    breakpoint()
    parser = Parser()
    parser.add_bpmn_files(bpmn_files)
    if dmn_files:
        parser.add_dmn_files(dmn_files)
    return BpmnWorkflow(parser.get_spec(process), subprocess_specs=parser.get_subprocess_specs(process), script_engine=CustomScriptEngine)

def select_option(prompt, options):

    option = input(prompt)
    while option not in options:
        print("Invalid selection")
        option = input(prompt)
    return option

def display_task(task):

    print(f'\n{task.task_spec.description}')
    if task.task_spec.documentation is not None:
        template = Template(task.task_spec.documentation)
        print(template.render(task.data))

def format_task(task, include_state=True):
    
    if hasattr(task.task_spec, 'lane') and task.task_spec.lane is not None:
        lane = f'[{task.task_spec.lane}]' 
    else:
        lane = ''
    state = f'[{task.get_state_name()}]' if include_state else ''
    return f'{lane} {task.task_spec.description} ({task.task_spec.name}) {state}'

def complete_user_task(task):

    display_task(task)
    if task.data is None:
        task.data = {}

    for field in task.task_spec.form.fields:
        if isinstance(field, EnumFormField):
            option_map = dict([ (opt.name, opt.id) for opt in field.options ])
            options = "(" + ', '.join(option_map) + ")"
            prompt = f"{field.label} {options} "
            option = select_option(prompt, option_map.keys())
            response = option_map[option]
        else:
            response = input(f"{field.label} ")
            if field.type == "long":
                response = int(response)
        task.update_data_var(field.id, response)

def complete_manual_task(task):

    display_task(task)
    input("Press any key to mark task complete")

def print_state(workflow: Workflow):

    task = workflow.last_task
    print('\nLast Task')
    print(format_task(task))
    print(json.dumps(task.data, indent=2, separators=[ ', ', ': ' ]))

    display_types = (UserTask, ManualTask, ScriptTask, ThrowingEvent, CatchingEvent, ServiceTask)
    all_tasks = [ task for task in workflow.get_tasks() if isinstance(task.task_spec, display_types) ]
    upcoming_tasks = [ task for task in all_tasks if task.state in [TaskState.READY, TaskState.WAITING] ]

    print('\nUpcoming Tasks')
    for idx, task in enumerate(upcoming_tasks):
        print(format_task(task))

    print('\All Tasks')
    for idx, task in enumerate(all_tasks):
        print(format_task(task))

def run(workflow: BpmnWorkflow, step):
    workflow.do_engine_steps()
    print(serializer.serialize_json(workflow))
    breakpoint()

    while not workflow.is_completed():

        ready_tasks = workflow.get_ready_user_tasks()
        options = { }
        print()
        for idx, task in enumerate(ready_tasks):
            option = format_task(task, False)
            options[str(idx + 1)] = task
            print(f'{idx + 1}. {option}')

        selected = None
        while selected not in options and selected not in ['', 'D', 'd']:
            selected = input('Select task to complete, enter to wait, or D to dump the workflow state: ')

        if selected.lower() == 'd':
            filename = input('Enter filename: ')
            state = serializer.serialize_json(workflow)
            with open(filename, 'w') as dump:
                dump.write(state)
        elif selected != '':
            next_task = options[selected]
            if isinstance(next_task.task_spec, UserTask):
                complete_user_task(next_task)
                next_task.complete()
            elif isinstance(next_task.task_spec, ManualTask):
                complete_manual_task(next_task)
                next_task.complete()
            else:
                next_task.complete()

        workflow.refresh_waiting_tasks()
        workflow.do_engine_steps()
        if step:
            print_state(workflow)

    print(serializer.serialize_json(workflow))
    print('\nWorkflow Data')
    print(json.dumps(workflow.data, indent=2, separators=[ ', ', ': ' ]))

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Simple BPMN runner')
    parser.add_argument('-p', '--process', dest='process', help='The top-level BPMN Process ID')
    parser.add_argument('-b', '--bpmn', dest='bpmn', nargs='+', help='BPMN files to load')
    parser.add_argument('-d', '--dmn', dest='dmn', nargs='*', help='DMN files to load')
    parser.add_argument('-r', '--restore', dest='restore', metavar='FILE',  help='Restore state from %(metavar)s')
    parser.add_argument('-s', '--step', dest='step', action='store_true', help='Display state after each step')
    args = parser.parse_args()

    try:
        if args.restore is not None:
            with open(args.restore) as state:
                wf = serializer.deserialize_json(state.read())
        else:
            wf = parse(args.process, args.bpmn, args.dmn)
        run(wf, args.step)
    except Exception as exc:
        sys.stderr.write(traceback.format_exc())
        sys.exit(1)
