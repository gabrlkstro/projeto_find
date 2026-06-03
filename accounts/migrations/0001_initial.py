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
                    name='Profile',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('image', models.ImageField(default='profile_pics/user.png', upload_to='profile_pics')),
                        ('telefone', models.CharField(blank=True, max_length=20, null=True)),
                        ('cidade', models.CharField(blank=True, max_length=100, null=True)),
                        ('estado', models.CharField(blank=True, max_length=2, null=True)),
                        ('data_nascimento', models.DateField(blank=True, null=True)),
                        ('cep', models.CharField(blank=True, max_length=9, null=True)),
                        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'mainpage_profile',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
