from __future__ import unicode_literals

from django.contrib.gis.db import models

class Shpfile(models.Model):
    filename = models.CharField(max_length=255)
    srs_wkt = models.CharField(max_length=255)
    geom_type = models.CharField(max_length=50)
    encoding = models.CharField(max_length=50)
    def __unicode__(self):
        return self.filename

class Attribute(models.Model):
    shpfile = models.ForeignKey(Shpfile)
    name = models.CharField(max_length=255)
    type = models.IntegerField()
    width = models.IntegerField()
    def __unicode__(self):
        return self.name

class Feature(models.Model):
    shpfile = models.ForeignKey(Shpfile)
    geom_point = models.PointField(srid=4326, blank=True, null=True)
    geom_multipoint = models.MultiPointField(srid=4326, blank=True, null=True)
    def __unicode__(self):
        return str(self.id)

class AttributeValue(models.Model):
    feature = models.ForeignKey(Feature)
    attribute = models.ForeignKey(Attribute)
    value = models.CharField(max_length=255, blank=True, null=True)
    def __unicode__(self):
        return self.value




