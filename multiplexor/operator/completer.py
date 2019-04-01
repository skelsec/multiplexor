
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

completer = WordCompleter([
	'connect','plugin','disconnect','exit'
	
	], ignore_case=True)

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})
