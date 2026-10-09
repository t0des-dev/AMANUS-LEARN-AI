from rest_framework import serializers

from .models import AudioContent


class AudioContentSerializer(serializers.ModelSerializer):
    audio_url = serializers.SerializerMethodField()
    section_title = serializers.CharField(source="section.title", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = AudioContent
        fields = (
            "id",
            "course_id",
            "course_title",
            "section_id",
            "section_title",
            "language",
            "voice_provider",
            "voice_id",
            "script",
            "storage_key",
            "duration",
            "status",
            "error_message",
            "audio_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "course_id",
            "section_id",
            "storage_key",
            "duration",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        )

    def get_audio_url(self, obj: AudioContent) -> str | None:
        return obj.get_audio_url()


class AudioGenerateRequestSerializer(serializers.Serializer):
    voice_provider = serializers.CharField(required=False, default="mock")
    voice_id = serializers.CharField(required=False, default="alloy")
    language = serializers.CharField(required=False, default="fr")
    custom_script = serializers.CharField(required=False, allow_blank=True, default="")


class VoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    language = serializers.CharField()
    gender = serializers.CharField()
    provider = serializers.CharField()
    description = serializers.CharField()
