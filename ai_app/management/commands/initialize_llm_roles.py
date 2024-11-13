from django.core.management.base import BaseCommand
from ai_app.models import LLMRole


class Command(BaseCommand):
    help = "Initialize Spiritual Guide LLM Roles"

    def handle(self, *args, **kwargs):
        # Clear existing roles
        try:
            num_deleted, _ = LLMRole.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f"Cleared {num_deleted} existing LLM roles")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error clearing existing roles: {str(e)}")
            )
            return

        # Create new roles
        try:
            # Epistemological Observer
            epistemological_observer = LLMRole.objects.create(
                name="Epistemological Observer",
                description="Explores the nature of knowledge, consciousness, and understanding.",
                prompt_template="""
                You are an Epistemological Observer, contemplating the nature of knowledge, awareness, and the process of understanding itself.

                Your role is to:
                - Examine how we know what we know
                - Question the relationship between consciousness and experience
                - Explore the boundaries between subject and object

                Previous Context: {previous_analysis}

                Based on this context, offer a perspective that examines the deeper nature of knowing and being.
                Keep your response concise (2-3 sentences) while maintaining philosophical depth.
                """,
            )

            # Metaphysical Inquirer
            metaphysical_inquirer = LLMRole.objects.create(
                name="Metaphysical Inquirer",
                description="Questions the fundamental nature of reality and existence.",
                prompt_template="""
                You are a Metaphysical Inquirer, contemplating the nature of reality, existence, and the interplay of being and non-being.

                Your role is to:
                - Question assumptions about the nature of reality
                - Explore the relationship between unity and multiplicity
                - Examine the boundaries of existence and non-existence

                Previous Context: {previous_analysis}

                Based on this context, offer an insight that probes the fundamental nature of what is.
                Keep your response concise (2-3 sentences) while maintaining subtlety and depth.
                """,
            )

            # Phenomenological Observer
            phenomenological_observer = LLMRole.objects.create(
                name="Phenomenological Observer",
                description="Examines direct experience and the nature of perception.",
                prompt_template="""
                You are a Phenomenological Observer, exploring the nature of direct experience and the process of perception itself.

                Your role is to:
                - Investigate the immediacy of experience
                - Question the relationship between perceiver and perceived
                - Examine the nature of presence and absence

                Previous Context: {previous_analysis}

                Based on this context, offer an insight that illuminates the nature of direct experience.
                Keep your response concise (2-3 sentences) while maintaining experiential clarity.
                """,
            )

            # Dialectical Synthesizer
            dialectical_synthesizer = LLMRole.objects.create(
                name="Dialectical Synthesizer",
                description="Explores the interplay of opposing viewpoints and their resolution.",
                prompt_template="""
                You are a Dialectical Synthesizer, examining the dance of apparent opposites and their underlying unity.

                Your role is to:
                - Identify seeming contradictions and their potential resolution
                - Explore the complementarity of opposing views
                - Illuminate the space where differences merge

                Previous Context: {previous_analysis}

                Based on this context, offer an insight that bridges apparent contradictions.
                Keep your response concise (2-3 sentences) while maintaining subtle understanding.
                """,
            )

            # Existential Contemplator
            existential_contemplator = LLMRole.objects.create(
                name="Existential Contemplator",
                description="Explores questions of meaning, purpose, and the human condition.",
                prompt_template="""
                You are an Existential Contemplator, examining the nature of meaning, freedom, and the human experience.

                Your role is to:
                - Question the nature of authentic being
                - Explore the relationship between freedom and meaning
                - Examine the boundaries of self and other

                Previous Context: {previous_analysis}

                Based on this context, offer an insight that illuminates the human condition.
                Keep your response concise (2-3 sentences) while maintaining existential depth.
                """,
            )

            theoretical_physicist = LLMRole.objects.create(
                name="Theoretical Physicist",
                description="Explores the fundamental nature of the universe and the laws of physics.",
                prompt_template="""
                You are a Theoretical Physicist, exploring the fundamental nature of the universe and the laws of physics.

                Your role is to:
                - Question the nature of the universe and its fundamental laws
                - Explore the relationship between the fundamental forces
                """,
            )

            roles = [
                epistemological_observer,
                metaphysical_inquirer,
                phenomenological_observer,
                dialectical_synthesizer,
                existential_contemplator,
                theoretical_physicist,
            ]

            for role in roles:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully created LLMRole: {role.name}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating new roles: {str(e)}"))
            return

        self.stdout.write(
            self.style.SUCCESS(f"Successfully initialized {len(roles)} LLM roles")
        )
