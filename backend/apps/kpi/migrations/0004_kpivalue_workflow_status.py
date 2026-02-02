from django.conf import settings
from django.db import migrations, models


def set_initial_status(apps, schema_editor):
    KpiValue = apps.get_model('kpi', 'KpiValue')
    for value in KpiValue.objects.all():
        if value.is_verified:
            value.status = 'approved'
            if not value.submitted_at:
                value.submitted_at = value.created_at
            if not value.reviewed_at:
                value.reviewed_at = value.updated_at
        else:
            value.status = 'draft'
            value.submitted_at = None
            value.reviewed_at = None
        value.save(update_fields=['status', 'submitted_at', 'reviewed_at'])


class Migration(migrations.Migration):
    dependencies = [
        ('kpi', '0003_alter_kpigroup_id_alter_kpiindicator_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='kpivalue',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('submitted', 'Submitted'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                default='draft',
                max_length=20,
                verbose_name='Status',
            ),
        ),
        migrations.AddField(
            model_name='kpivalue',
            name='submitted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='kpivalue',
            name='reviewer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='reviewed_kpi_values',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='kpivalue',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='kpivalue',
            name='review_comment',
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(set_initial_status, migrations.RunPython.noop),
    ]
