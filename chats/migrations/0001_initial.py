"""
Migration state-only: registra Chat e Mensagem no app chats sem criar tabelas.
As tabelas mainpage_chat e mainpage_mensagem já existem no banco.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Chat',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('criado_em', models.DateTimeField(auto_now_add=True)),
                        ('atualizado_em', models.DateTimeField(auto_now=True)),
                        ('status', models.CharField(choices=[('ativo', 'Ativo'), ('fechado', 'Fechado')], default='ativo', max_length=20)),
                        ('item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chats', to='items.item')),
                        ('criado_por', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chats_criados', to=settings.AUTH_USER_MODEL)),
                        ('dono_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chats_como_dono', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'mainpage_chat',
                    },
                ),
                migrations.CreateModel(
                    name='Mensagem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('conteudo', models.TextField(max_length=200)),
                        ('data_envio', models.DateTimeField(auto_now_add=True)),
                        ('tipo', models.CharField(choices=[('texto', 'Texto'), ('imagem', 'Imagem')], default='texto', max_length=20)),
                        ('lida', models.BooleanField(default=False)),
                        ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensagens', to='chats.chat')),
                        ('remetente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'mainpage_mensagem',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
