extends SceneTree
# Measures strings with the FontFile resources build_all.gd wrote, and prints
# the widths as JSON for the Python side to compare against its own metrics.
#
# This is the one check in the export that exercises the ENGINE rather than the
# file. The nine-slice round-trip re-reads margins out of a .tres and confirms
# they are the numbers that were drawn, which catches a reordering and cannot
# catch a resource Godot loads and then lays out wrongly. Text has a way out of
# that: `get_string_size` runs on TextServer, not on the renderer, so it works
# in a headless build -- and it is the same code path a Label uses. If Godot
# agrees with `bitmap_font.measure` on where every glyph ends up, the advances,
# the cell arithmetic and the space glyph are all right together.

func _init():
	var samples := ["Flat White", "iiii", "MMMM", "Latte x2", "A B C",
		"gjpqy", "0123456789", "Morning!"]
	var out := {}
	var dir := DirAccess.open("res://resources/font")
	if dir == null:
		printerr("no res://resources/font")
		quit(1)
		return
	for file in dir.get_files():
		if not file.ends_with(".tres"):
			continue
		var f: FontFile = load("res://resources/font/%s" % file)
		if f == null:
			printerr("failed to load ", file)
			continue
		var cap := f.fixed_size
		var widths := {}
		for s in samples:
			widths[s] = f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, cap).x
		out[str(cap)] = widths
	print("VERIFY_FONT_JSON:", JSON.stringify(out))
	quit(0)
