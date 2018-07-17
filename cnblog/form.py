from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms import widgets


class UserForm(forms.Form):
    name = forms.CharField(min_length=4, max_length=12, label="姓名",
                           widget=widgets.TextInput(attrs={"class": "form-control"}),
                            error_messages = {"required": "该字段不能为空"}
                           )
    age = forms.IntegerField(label="年龄",
                             error_messages={"invalid": "格式错误"},
                             widget=widgets.TextInput(attrs={"class": "form-control"}))
    telephone = forms.CharField(label="电话号码",
                                widget=widgets.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label="邮箱",
                             widget=widgets.EmailInput(attrs={"class": "form-control"}))
    pwd = forms.CharField(min_length=6, label="密码",
                          widget=widgets.PasswordInput(attrs={"class": "form-control"}))
    r_pwd = forms.CharField(label="确认密码",
                            widget=widgets.PasswordInput(attrs={"class": "form-control"})
                            )


    def clean_name(self):

        val = self.cleaned_data.get("name")
        if not val.isdigit():
            return val
        else:
            raise ValidationError('用户名不能是纯数字')
    def clean_telephone(self):
        val = self.cleaned_data.get("telephone")
        if len(val) == 11:
            return val
        else:
            raise ValidationError("手机号码错了")
    def clean_age(self):
        val = self.cleaned_data.get("age")
        if int(val)>18:
            return val
        else:
            raise ValidationError("岁数太小的")

    def clean(self):
        pwd = self.cleaned_data.get('pwd')
        r_pwd = self.cleaned_data.get("r_pwd")
        if pwd and r_pwd and pwd!=r_pwd:
            raise ValidationError("两次密码不一致")
        else:
            return self.cleaned_data