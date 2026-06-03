from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainpage', '0005_remove_chat_unique_chat_por_item_e_usuarios_and_more'),
        ('accounts', '0001_initial'),
        ('items', '0001_initial'),
        ('chats', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='Mensagem'),
                migrations.DeleteModel(name='Chat'),
                migrations.DeleteModel(name='Item'),
                migrations.DeleteModel(name='Categoria'),
                migrations.DeleteModel(name='Profile'),
            ],
            database_operations=[],
        ),
    ]
