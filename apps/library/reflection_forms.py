from django import forms
from django.utils.translation import gettext_lazy as _


class StrictForm(forms.Form):
    def clean(self):
        cleaned = super().clean()
        allowed = set(self.fields) | {"csrfmiddlewaretoken"}
        if self.is_bound and (set(self.fields) - set(self.data) or set(self.data) - allowed or any(
            len(self.data.getlist(key)) != 1 for key in self.data
        )):
            raise forms.ValidationError(_("Formular invalid. Trimite doar câmpurile afișate, o singură dată."))
        return cleaned


class StartReflectionForm(StrictForm):
    revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)


class ReflectionAnswersForm(StrictForm):
    revision = forms.IntegerField(min_value=1, widget=forms.HiddenInput)

    def __init__(self, *args, rows, **kwargs):
        self.rows = rows
        super().__init__(*args, **kwargs)
        for row in rows:
            position = row["position"]
            self.fields[f"question_{position}"] = forms.IntegerField(
                initial=row["question_id"], widget=forms.HiddenInput,
            )
            self.fields[f"answer_{position}"] = forms.CharField(
                label=row["question"], required=False, max_length=2000, strip=False,
                initial=row["answer"], widget=forms.Textarea(attrs={
                    "rows": 5, "maxlength": 2000, "class": "form-control",
                    "style": "width:100%;min-height:140px;font-size:1rem;resize:vertical;box-sizing:border-box;",
                    "aria-describedby": f"reflection-hint-{position}",
                }),
            )

    def clean(self):
        cleaned = super().clean()
        if len(self.rows) != 4 or any(cleaned.get(f"question_{row['position']}") != row["question_id"] for row in self.rows):
            raise forms.ValidationError(_("Întrebările nu corespund setului salvat. Reîncarcă pagina."))
        if not any(cleaned.get(f"answer_{position}", "").strip() for position in range(1, 5)):
            raise forms.ValidationError(_("Scrie cel puțin un răspuns înainte de salvare."))
        return cleaned

    def question_fields(self):
        return [{**row, "id_field": self[f"question_{row['position']}"],
                 "answer_field": self[f"answer_{row['position']}"]} for row in self.rows]
