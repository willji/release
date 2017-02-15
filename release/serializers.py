from rest_framework import serializers
from release.models import Type, Step, Mission, Progress, Log_progress, Status, Type_step, Mission_control


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type


class Type_stepSerializer(serializers.ModelSerializer):
    type = serializers.SlugRelatedField(queryset=Type.objects.all(), slug_field='alias')
    step = serializers.SlugRelatedField(queryset=Step.objects.all(), slug_field='alias')

    class Meta:
        model = Type_step
        # fields=('step','order')


class MissionSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.SlugRelatedField(queryset=Type.objects.all(), slug_field='alias')

    class Meta:
        model = Mission
        fields = ('url', 'mark', 'version', 'type', 'dep', 'item', 'item_type', 'env', 'status', 'percent', 'host_failed', 'timeout_status', 'creator', 'modified_date', 'created_date')


class ProgressSerializer(serializers.ModelSerializer):
    status = serializers.SlugRelatedField(queryset=Status.objects.all(), slug_field='alias')
    type = serializers.SlugRelatedField(queryset=Type.objects.all(), slug_field='alias')
    step = serializers.SlugRelatedField(queryset=Step.objects.all(), slug_field='alias')

    class Meta:
        model = Progress


class LogProgressSerializer(serializers.ModelSerializer):
    status = serializers.SlugRelatedField(queryset=Status.objects.all(), slug_field='alias')
    type = serializers.SlugRelatedField(queryset=Type.objects.all(), slug_field='alias')
    step = serializers.SlugRelatedField(queryset=Step.objects.all(), slug_field='alias')

    class Meta:
        model = Log_progress


class MissionControlSerializer(serializers.ModelSerializer):
    status = serializers.SlugRelatedField(queryset=Status.objects.all(), slug_field='alias')
    host = serializers.IntegerField(read_only=True)
    host_done = serializers.IntegerField(read_only=True)
    order = serializers.IntegerField(read_only=True)
    times = serializers.IntegerField(read_only=True)
    gray_status = serializers.BooleanField(read_only=True)
    lock_status = serializers.BooleanField(read_only=True)
    mission = serializers.CharField(read_only=True)

    class Meta:
        model = Mission_control
