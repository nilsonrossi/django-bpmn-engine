# Generated by Django 4.0 on 2022-08-20 21:54

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('xml', models.TextField()),
                ('workflow_process_id', models.CharField(max_length=100)),
                ('version', models.PositiveSmallIntegerField(default=1)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Workflow',
                'verbose_name_plural': 'Workflows',
            },
        ),
        migrations.CreateModel(
            name='WorkflowInstance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('instance_id', models.CharField(max_length=100)),
                ('state', models.CharField(choices=[('RUNNING', 'Running'), ('COMPLETED', 'Completed'), ('CANCELED', 'Canceled')], default='RUNNING', max_length=20, verbose_name='State')),
                ('workflow_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='core.workflow')),
            ],
            options={
                'verbose_name': 'WorkflowInstance',
                'verbose_name_plural': 'WorkflowInstances',
            },
        ),
    ]