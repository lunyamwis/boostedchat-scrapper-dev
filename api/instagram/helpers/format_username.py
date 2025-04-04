import emoji

def format_full_name(full_name):
  subject = full_name
  if subject == "" or subject is None:
    return "there"
  stripped = emoji.replace_emoji(subject, '')
  stripped_list = stripped.split(" ")
  return stripped_list[0]
