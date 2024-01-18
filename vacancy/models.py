from django.db import models


class DemandTables(models.Model):
    name = models.CharField(max_length=255)
    table_content = models.CharField(max_length=1024)

    class Meta:
        verbose_name = 'demand_table'

    def __str__(self):
        return self.name


class GeographyTables(models.Model):
    name = models.CharField(max_length=255)
    table_content = models.CharField(max_length=1024)

    class Meta:
        verbose_name = 'geography_table'

    def __str__(self):
        return self.name


class SkillsTables(models.Model):
    name = models.CharField(max_length=255)
    table_content = models.CharField(max_length=1024)

    class Meta:
        verbose_name = 'skills_table'

    def __str__(self):
        return self.name


class Graphics(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField()

    def __str__(self):
        return self.name
