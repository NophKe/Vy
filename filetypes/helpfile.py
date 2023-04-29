from vy.filetypes.textfile import TextFile

class HelpFile(TextFile):
	@property
	def _string(self):
		return self._init_text
	@string.setter
	def _string(self, value):
		return
