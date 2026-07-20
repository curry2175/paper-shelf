from django import template

register = template.Library()


@register.filter
def book_hue(value):
    text = str(value or "paper")
    return sum((index + 1) * ord(char) for index, char in enumerate(text)) % 360
