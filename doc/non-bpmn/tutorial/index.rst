Tutorial - Non-BPMN
===================

Introduction
------------

In this chapter we are going to use Spiff Workflow to solve a real-world
problem: We will create a workflow for triggering a nuclear strike.

We are assuming that you are familiar with the :doc:`../basics`.

Assume you want to send the rockets, but only after both the president and
a general have signed off on it.

There are two different ways of defining a workflow: Either by deserializing
(from XML or JSON), or using Python.

Creating the workflow specification (using Python)
--------------------------------------------------

As a first step, we are going to create a simple workflow in code.
In Python, the workflow is defined as follows:

.. literalinclude:: nuclear.py

Hopefully the code is self explaining.
Using Python to write a workflow can quickly become tedious. It is
usually a better idea to use another format.

Creating a workflow specification (using JSON)
----------------------------------------------

Once you have completed the serializer as shown above, you can
write the specification in JSON.

Here is an example that is doing exactly the same as the Python
WorkflowSpec above:

.. literalinclude:: nuclear.json

Creating a workflow out of the specification
--------------------------------------------

Now it is time to get started and actually create and execute
a workflow according to the specification.

Since we included *manual* tasks in the specification, you will want
to implement a user interface in practice, but we are just going to
assume that all tasks are automatic for this tutorial.
Note that the *manual* flag has no effect on the control flow; it is
just a flag that a user interface may use to identify tasks that
require a user input.

.. literalinclude:: start.py

:meth:`py_bpmn_engine.Workflow.complete_all` completes all tasks in
accordance to the specification, until no further tasks are READY
for being executed.
Note that this does not mean that the workflow is completed after
calling :meth:`py_bpmn_engine.Workflow.complete_all`, since some
tasks may be WAITING, or may be blocked by another WAITING task,
for example.


Serializing a workflow
----------------------

If you want to store a :class:`py_bpmn_engine.specs.WorkflowSpec`, you can
use :meth:`py_bpmn_engine.specs.WorkflowSpec.serialize`:

.. literalinclude:: serialize.py

If you want to store a :class:`py_bpmn_engine.Workflow`, use
use :meth:`py_bpmn_engine.Workflow.serialize`:

.. literalinclude:: serialize-wf.py

Deserializing a workflow
------------------------

The following example shows how to restore a
:class:`py_bpmn_engine.specs.WorkflowSpec` using
:meth:`py_bpmn_engine.specs.WorkflowSpec.serialize`.

.. literalinclude:: deserialize.py

To restore a :class:`py_bpmn_engine.Workflow`, use
:meth:`py_bpmn_engine.Workflow.serialize` instead:

.. literalinclude:: deserialize-wf.py

Where to go from here?
----------------------

This first tutorial actually has a problem: If you want to save the workflow,
py_bpmn_engine won't be able to re-connect the signals because it can not
save the reference to your code.

So after deserializing the workflow, you will need to re-connect the signals
yourself.

If you would rather have it such that py_bpmn_engine handles this for you,
you need to create a custom task and tell py_bpmn_engine how to
serialize and deserialize it. The next tutorial shows how this is done.
