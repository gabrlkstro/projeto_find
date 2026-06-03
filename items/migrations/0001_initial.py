from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Categoria',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('nome', models.CharField(max_length=45)),
                        ('descricao', models.CharField(blank=True, max_length=45)),
                    ],
                    options={
                        'db_table': 'mainpage_categoria',
                    },
                ),
                migrations.CreateModel(
                    name='Item',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('titulo', models.CharField(max_length=45)),
                        ('slug', models.SlugField(blank=True, max_length=60, unique=True)),
                        ('descricao', models.CharField(max_length=200)),
                        ('status', models.CharField(choices=[('achado', 'Achado'), ('perdido', 'Perdido'), ('devolvido', 'Devolvido')], max_length=45)),
                        ('local', models.CharField(max_length=45)),
                        ('data', models.DateField()),
                        ('imagem', models.ImageField(blank=True, null=True, upload_to='itens/')),
                        ('criado_em', models.DateTimeField(auto_now_add=True)),
                        ('atualizado_em', models.DateTimeField(auto_now=True)),
                        ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to=settings.AUTH_USER_MODEL)),
                        ('categoria', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='items.categoria')),
                    ],
                    options={
                        'db_table': 'mainpage_item',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
