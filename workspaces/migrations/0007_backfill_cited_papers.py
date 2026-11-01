from django.db import migrations


def add_cited_papers(apps, schema_editor):
    MessageCitation = apps.get_model('workspaces', 'MessageCitation')
    WorkspacePaper = apps.get_model('workspaces', 'WorkspacePaper')
    pairs = set(MessageCitation.objects.values_list('message__workspace_id', 'chunk__paper_id'))
    WorkspacePaper.objects.bulk_create(
        (WorkspacePaper(workspace_id=workspace_id, paper_id=paper_id) for workspace_id, paper_id in pairs),
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0006_workspace_papers_only'),
    ]

    operations = [
        migrations.RunPython(add_cited_papers, migrations.RunPython.noop),
    ]
