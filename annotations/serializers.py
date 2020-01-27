from rest_framework import serializers
from annotations.models import VogonUser
from .models import *
from repository.models import Repository as RepositoryModel
from concepts.models import Concept, Type


class UserSerializer(serializers.ModelSerializer):
    annotation_count = serializers.IntegerField(allow_null=True)
    relation_count = serializers.IntegerField(allow_null=True)
    text_count = serializers.IntegerField(allow_null=True)

    class Meta:
        model = VogonUser
        fields = ('username', 'email', 'id', 'affiliation', 'location',
                  'full_name', 'link', 'is_admin', 'imagefile',
                  'annotation_count', 'relation_count', 'text_count')


class RemoteCollectionSerializer(serializers.Serializer):
    source = serializers.IntegerField()
    id_or_uri = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)


class RemoteResourceSerializer(serializers.Serializer):
    source = serializers.IntegerField()
    id_or_uri = serializers.CharField(max_length=255)
    title = serializers.CharField(max_length=255)


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RepositoryModel
        fields = '__all__'


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = '__all__'


class DocumentPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPosition
        fields = '__all__'


class DateAppellationSerializer(serializers.ModelSerializer):
    position = DocumentPositionSerializer(required=False)

    class Meta:
        model = DateAppellation
        fields = ('created', 'createdBy', 'id', 'occursIn', 'position', 'year',
                  'month', 'day', 'project', 'stringRep', 'dateRepresentation')


class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = ('id', 'uri', 'title', 'created', 'added', 'addedBy',
                  'source', 'annotators', 'annotation_count', 'children',
                  'repository_id', 'repository_source_id')

    def create(self, validated_data):
        repository = Repository.objects.get(pk=validated_data['source'])
        # TODO: Make retrieval/tokenization/other processing asynchronous.
        tokenizedContent = tokenize(
            retrieve(repository, validated_data['uri']))

        text = Text(
            uri=validated_data['uri'],
            title=validated_data['title'],
            source=repository,
            addedBy=self.context['request'].user,
            tokenizedContent=tokenizedContent)
        text.save()
        return HttpResponse(text.id)


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ('id', 'url', 'uri', 'label', 'authority', 'typed',
                  'description')


class ConceptSerializer(serializers.ModelSerializer):
    typed = TypeSerializer(required=False)

    class Meta:
        model = Concept
        fields = ('id', 'url', 'uri', 'label', 'authority', 'typed',
                  'description', 'pos', 'resolved', 'typed_label',
                  'concept_state', 'appellation_set', 'conceptpower_namespaced')

class ConceptLifecycleSerializer(serializers.Serializer):
    label = serializers.CharField(required=True)
    description = serializers.CharField(required=False)
    typed = serializers.CharField(required=False)
    uri = serializers.CharField(required=False)

class AppellationSerializer(serializers.ModelSerializer):
    position = DocumentPositionSerializer(required=False)
    tokenIds = serializers.CharField(required=False)
    stringRep = serializers.CharField(required=False)
    occursIn = TextSerializer(required=False)
    interpretation = ConceptSerializer(required=False)
    createdBy = UserSerializer()

    class Meta:
        model = Appellation
        fields = ('asPredicate', 'created', 'createdBy', 'endPos', 'id',
                  'interpretation', 'interpretation_type', 'occursIn',
                  'startPos', 'stringRep', 'tokenIds', 'interpretation_label',
                  'interpretation_type_label', 'position', 'project')

class AppellationPOSTSerializer(serializers.ModelSerializer):
    position = DocumentPositionSerializer(required=False)
    tokenIds = serializers.CharField(required=False)
    stringRep = serializers.CharField(required=False)

    class Meta:
        model = Appellation
        fields = ('asPredicate', 'created', 'createdBy', 'endPos', 'id',
                  'interpretation', 'interpretation_type', 'occursIn',
                  'startPos', 'stringRep', 'tokenIds', 'interpretation_label',
                  'interpretation_type_label', 'position', 'project')


class RelationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationTemplate
        fields = '__all__'


class RelationSetSerializer(serializers.ModelSerializer):
    class DateAppellationPredicateSerializer(serializers.BaseSerializer):
        def to_representation(self, obj):
            return {
                'interpretation': ConceptSerializer(obj[0], context=self.context).data,
                'appellation': DateAppellationSerializer(obj[1], context=self.context).data
            }
    appellations = AppellationSerializer(many=True)
    date_appellations = DateAppellationSerializer(many=True)
    concepts = ConceptSerializer(many=True)
    createdBy = UserSerializer()
    template = RelationTemplateSerializer()
    date_appellations_with_predicate = DateAppellationPredicateSerializer(many=True)
    occursIn = TextSerializer()
    created = serializers.DateTimeField()

    class Meta:
        model = RelationSet
        fields = ('id', 'label', 'created', 'template', 'createdBy',
                  'occursIn', 'appellations', 'concepts', 'project',
                  'representation', 'date_appellations', 'submitted',
                  'submittedOn', 'pending', 'ready', 'template',
                  'date_appellations_with_predicate', 'occurs_in_text',
                  'terminal_nodes')  #


class TemporalBoundsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporalBounds
        fields = '__all__'


class TextCollectionSerializer(serializers.ModelSerializer):
    class VogonUserSerializer(serializers.ModelSerializer):
        class Meta:
            model = VogonUser
            fields = ['id', 'username']
    
    ownedBy = VogonUserSerializer()
    num_texts = serializers.IntegerField()
    num_relations = serializers.IntegerField()
    
    class Meta:
        model = TextCollection
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextCollection
        fields = '__all__'


class ProjectTextSerializer(TextCollectionSerializer):
    class TextSerializer(serializers.ModelSerializer):
        class Meta:
            model = Text
            fields = ['id', 'title', 'added', 'repository_id', 'repository_source_id']
    texts = TextSerializer(many=True, read_only=True)

class TemplateFieldsSerializer(serializers.Serializer):
    part_field = serializers.CharField(max_length=200, required=False)
    concept_label = serializers.CharField(max_length=200, required=False)
    part_id = serializers.IntegerField()
    evidence_required = serializers.BooleanField(default=False)
    description = serializers.CharField(max_length=2000, required=False)
    type = serializers.CharField(max_length=100, required=False)
    concept_id = serializers.IntegerField(required=False)
    label = serializers.CharField(max_length=200, required=False)


class TemplatePartSerializer(serializers.ModelSerializer):
    fields = TemplateFieldsSerializer(many=True, default=[])
    class Meta:
        model = RelationTemplate
        fields = ('id', 'name', 'description', 'fields')


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationTemplate
        fields = ('id', 'name', 'created', 'description', 'expression', 'terminal_nodes', 'template_parts')
        depth = 2

class TextAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = '__all__'
        depth = 1


class Concept2Serializer(serializers.Serializer):
    
    id = serializers.IntegerField()
    #url = serializers.CharField()
    uri = serializers.CharField()
    label = serializers.CharField()
    authority = serializers.CharField()
    typed = TypeSerializer()
    description = serializers.CharField()
    pos = serializers.CharField()
    resolved = serializers.BooleanField()
    typed_label = serializers.CharField()
    # class Meta:
    #     model = Concept
    #     fields = ('id', 'url', 'uri', 'label', 'authority', 'typed',
    #               'description', 'pos', 'resolved', 'typed_label')


class Appellation2Serializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    position = DocumentPositionSerializer(required=False)
    tokenIds = serializers.CharField(required=False)
    stringRep = serializers.CharField(required=False)
    occursIn = TextAllSerializer(required=False)
    interpretation = Concept2Serializer(required=False)
    createdBy = UserSerializer()


class Text2Serializer(serializers.Serializer):
    text = TextAllSerializer()
    textid = serializers.IntegerField(read_only=True)
    title = serializers.CharField()
    content = serializers.CharField()
    baselocation = serializers.CharField()
    userid = serializers.IntegerField(read_only=True)
    repository_id =  serializers.IntegerField(read_only=True)
    project = ProjectSerializer()
    appellations = Appellation2Serializer(many=True)
    relations = RelationSerializer(many=True)
