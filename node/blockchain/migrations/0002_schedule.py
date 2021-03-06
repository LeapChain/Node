# Generated by Django 3.2.9 on 2021-12-11 19:30

from django.db import migrations, models

import node.blockchain.validators


class Migration(migrations.Migration):

    dependencies = [
        ('blockchain', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                (
                    '_id',
                    models.PositiveBigIntegerField(primary_key=True, serialize=False, verbose_name='Block number')
                ),
                (
                    'node_identifier',
                    models.CharField(max_length=64, validators=[node.blockchain.validators.HexStringValidator(64)])
                ),
            ],
        ),
    ]
