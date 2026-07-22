from django import forms

from deals.models import Stage
from tasks.models import Task

from .models import AutomationRule


class AutomationRuleForm(forms.ModelForm):
    class Meta:
        model = AutomationRule
        fields = [
            "name",
            "is_active",
            "trigger",
            "trigger_stage",
            "no_activity_days",
            "action",
            "action_target_stage",
            "task_type",
            "task_title",
            "task_due_in_hours",
        ]

    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["trigger"].choices = AutomationRule.Trigger.choices
        self.fields["action"].choices = AutomationRule.Action.choices
        stages = Stage.objects.filter(pipeline__organization=organization)
        self.fields["trigger_stage"].queryset = stages
        self.fields["trigger_stage"].required = False
        self.fields["trigger_stage"].empty_label = "Не выбран"
        self.fields["action_target_stage"].queryset = stages
        self.fields["action_target_stage"].required = False
        self.fields["action_target_stage"].empty_label = "Не выбран"
        self.fields["task_type"].required = False
        self.fields["task_type"].choices = [("", "Не применимо")] + list(Task.Type.choices)
        self.fields["task_title"].required = False
        self.fields["no_activity_days"].required = False
