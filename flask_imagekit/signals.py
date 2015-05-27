from blinker import Namespace

imagekit_signals = Namespace()

# Generated file signals
content_required = imagekit_signals.signal('content_required')
existence_required = imagekit_signals.signal('existence_required')

# Source group signals
source_saved = imagekit_signals.signal('source_saved')
