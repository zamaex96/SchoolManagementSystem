# core/forms.py

from django import forms
from .models import Result, Subject, SchoolClass # Import Result and Subject model
from django.core.exceptions import ValidationError # Import ValidationError

class ResultForm(forms.ModelForm):
    # Optional: If you want to ensure only relevant subjects are shown,
    # you might override the 'subject' field's queryset here or in the view.
    # For now, we'll let it show all subjects.
    # subject = forms.ModelChoiceField(queryset=Subject.objects.all(), widget=forms.Select)

    class Meta:
        model = Result
        # Fields to include in the form
        fields = ['subject', 'term_exam_name', 'score', 'grade', 'comments']
        # Add widgets for better presentation if needed (e.g., Textarea for comments)
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 3}),
            # Example: If using Bootstrap, add form-control class
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'term_exam_name': forms.TextInput(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}), # Allow decimals
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            # 'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), # Add class here too
        }
        labels = {
            'term_exam_name': 'Term / Exam Name', # Nicer label
        }

    # --- ADD VALIDATION METHOD ---
    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None:  # Only validate if score is provided
            if score < 0 or score > 100:  # Example range
                raise ValidationError("Score must be between 0 and 100.")
        return score

    # Optional: Validate that score OR grade is entered?
    # def clean(self):
    #     cleaned_data = super().clean()
    #     score = cleaned_data.get("score")
    #     grade = cleaned_data.get("grade")
    #     if score is None and not grade: # Check if both are empty/None
    #          raise ValidationError("Please enter either a Score or a Grade.")
    #     return cleaned_data
    # --- END VALIDATION ---

# --- ADD NEW FORM FOR ADMIN ACTION ---
class AssignClassForm(forms.Form):
    # Use ModelChoiceField to get a dropdown of existing classes
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all().order_by('-academic_year', 'name'), # Sensible ordering
        required=True,
        label="Assign selected students to class"
    )
    # You might add options here later, e.g., a checkbox to clear previous class assignments