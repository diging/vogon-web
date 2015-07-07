from rest_framework import serializers
from django.contrib.auth.models import User
from models import *
from concepts.models import Concept

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation


class AppellationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appellation
#
#    def validate_interpretation(self, value):
#        print 'asdf'
#        print value
#        return super(AppellationSerializer, self).validate_interpretation(value)


class TemporalBoundsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporalBounds


class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ('id', 'url', 'uri', 'label', 'authority', 'type')

