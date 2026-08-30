extends SceneTree
# Reads build_manifest.json (written by tools/package_godot.py) and builds one
# Godot resource per factory asset. Four producers, four resource shapes:
#
#   "assets"  static props   -> SpriteFrames, 8 AtlasTexture frames in one
#                               "idle" animation, indexed so game code can set
#                               `.frame = direction_index` directly -- there is
#                               no motion, just 8 fixed poses of a camera-fixed
#                               isometric rig
#   "anim"    characters/FX  -> SpriteFrames, one animation per (clip,
#                               direction) named "<clip>_<dir>", frames cut out
#                               of the packed sheet as AtlasTexture regions
#   "ui"      icons/chrome   -> nine-slice pieces become StyleBoxTexture with
#                               texture margins from the drawn insets; plain
#                               icons need no wrapper resource and are only
#                               load-checked, because the imported PNG already
#                               IS the Texture2D a Control wants
#   "font"    bitmap font    -> one FontFile per cap height, glyphs registered
#                               against the staged sheet so a Label can set any
#                               string -- a font resource, not baked strings
#   "tiles"   ground tiles   -> one TileSet holding a TileSetAtlasSource per
#                               tile type, isometric diamond-down, with the
#                               tile size read from the manifest rather than
#                               restated -- tileset.py derives it from the
#                               camera basis and proves the tiling
#
# World-space facts (height, footprint, anchor, walkable) and per-direction
# facts (pivot, bbox, azimuth) that have no native SpriteFrames slot are
# carried as resource metadata so downstream GDScript can read them back with
# `get_meta()`.
#
# Must run AFTER a `--headless --import` pass on this project (the PNGs under
# assets/ have to already be real, file-backed Texture2D resources -- see
# ART_CRITIQUE.md / NEXT.md "Godot export" notes for why: an un-imported PNG
# loaded via Image.load()+ImageTexture.create_from_image() serializes as a
# bloated inline pixel blob instead of a lightweight ext_resource path).

var failed := []


func _init():
	var f := FileAccess.open("res://build_manifest.json", FileAccess.READ)
	if f == null:
		printerr("build_manifest.json not found -- run tools/package_godot.py first")
		quit(1)
		return
	var data = JSON.parse_string(f.get_as_text())
	f.close()
	if data == null:
		printerr("build_manifest.json: invalid JSON")
		quit(1)
		return

	_mkdir("res://resources")
	var n_props := _build_props(data.get("assets", {}))
	var n_anim := _build_anim(data.get("anim", {}))
	var n_ui := _build_ui(data.get("ui", {}))
	var n_tiles := _build_tiles(data.get("tiles", {}))
	var n_font := _build_font(data.get("font", {}))

	print("built ", n_props, " prop SpriteFrames, ", n_anim,
		" animation SpriteFrames, ", n_ui, " UI resources, ", n_tiles,
		" tile sources, ", n_font, " fonts in res://resources")
	if failed.size() > 0:
		printerr("failed: ", failed)
		quit(1)
		return
	quit(0)


func _mkdir(path: String) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path))


func _load_tex(path: String, owner: String) -> Texture2D:
	var tex: Texture2D = load(path)
	if tex == null:
		printerr(owner, ": failed to load ", path, " (import missing?)")
		failed.append(owner)
	return tex


func _save(res: Resource, path: String, owner: String) -> bool:
	var err = ResourceSaver.save(res, path)
	if err != OK:
		printerr(owner, ": save failed, err ", err)
		failed.append(owner)
		return false
	return true


# --- static props ------------------------------------------------------------

func _build_props(assets: Dictionary) -> int:
	var ok := 0
	for asset_name in assets.keys():
		var entry = assets[asset_name]
		var frames := SpriteFrames.new()
		frames.remove_animation("default")
		frames.add_animation("idle")
		frames.set_animation_loop("idle", false)
		frames.set_animation_speed("idle", 0.0)

		var pivots := []
		var bboxes := []
		var azimuths := []
		var frame_list = entry["frames"]
		frame_list.sort_custom(func(a, b): return a["direction"] < b["direction"])
		var bad := false
		for fr in frame_list:
			var tex := _load_tex("res://assets/%s/%s" % [asset_name, fr["file"]], asset_name)
			if tex == null:
				bad = true
				continue
			var atlas := AtlasTexture.new()
			atlas.atlas = tex
			atlas.region = Rect2(Vector2.ZERO, tex.get_size())
			frames.add_frame("idle", atlas)
			pivots.append(fr["pivot"])
			bboxes.append(fr["bbox"])
			azimuths.append(fr["azimuth"])
		if bad:
			continue

		var world = entry["world"]
		frames.set_meta("height", world["height"])
		frames.set_meta("footprint_xy", world["footprint_xy"])
		frames.set_meta("anchor", world["anchor"])
		frames.set_meta("walkable", world["walkable"])
		frames.set_meta("pivots", pivots)
		frames.set_meta("bboxes", bboxes)
		frames.set_meta("azimuths", azimuths)

		if _save(frames, "res://resources/%s.tres" % asset_name, asset_name):
			ok += 1
	return ok


# --- animated characters and effects -----------------------------------------

func _build_anim(anim: Dictionary) -> int:
	if anim.is_empty():
		return 0
	_mkdir("res://resources/anim")
	var sheets = anim.get("sheets", {})
	var ok := 0
	for name in sheets.keys():
		var entry = sheets[name]
		var tex := _load_tex("res://assets/%s" % entry["file"], name)
		if tex == null:
			continue

		var frames := SpriteFrames.new()
		frames.remove_animation("default")
		var anchors := {}
		for clip in entry["clips"].keys():
			var meta = entry["clips"][clip]
			for dir_label in meta["regions"].keys():
				# One animation per (clip, direction). Godot has no native
				# notion of a facing, so the facing goes in the name; this is
				# what an AnimatedSprite2D can actually play, and it keeps the
				# row arithmetic on the Python side where it was checked.
				var anim_name := "%s_%s" % [clip, dir_label]
				frames.add_animation(anim_name)
				frames.set_animation_speed(anim_name, meta["fps"])
				frames.set_animation_loop(anim_name, true)
				for r in meta["regions"][dir_label]:
					var atlas := AtlasTexture.new()
					atlas.atlas = tex
					atlas.region = Rect2(r[0], r[1], r[2], r[3])
					frames.add_frame(anim_name, atlas)
			if meta.has("anchor"):
				anchors[clip] = meta["anchor"]

		frames.set_meta("kind", entry["kind"])
		frames.set_meta("sheet_size", entry["sheet_size"])
		if not anchors.is_empty():
			frames.set_meta("anchors", anchors)
		if entry.has("role"):
			frames.set_meta("role", entry["role"])
		if entry.has("symmetry"):
			frames.set_meta("symmetry", entry["symmetry"])

		if _save(frames, "res://resources/anim/%s.tres" % name, name):
			ok += 1
	return ok


# --- UI ----------------------------------------------------------------------

func _build_ui(ui: Dictionary) -> int:
	if ui.is_empty():
		return 0
	_mkdir("res://resources/ui")
	var icons = ui.get("icons", {})
	var ok := 0
	for id in icons.keys():
		var info = icons[id]
		var tex := _load_tex("res://assets/%s" % info["file"], id)
		if tex == null:
			continue
		if not info.has("nine_slice"):
			# A plain icon needs no wrapper: the imported PNG is already the
			# Texture2D a TextureRect or Button wants. Load-checking it is the
			# whole of what export means for these, and inventing a resource
			# to wrap it would be output for the sake of a count.
			ok += 1
			continue
		var ins = info["nine_slice"]
		var box := StyleBoxTexture.new()
		box.texture = tex
		box.texture_margin_left = ins[0]
		box.texture_margin_top = ins[1]
		box.texture_margin_right = ins[2]
		box.texture_margin_bottom = ins[3]
		# TILE, not STRETCH. `ui_chrome.expand()` repeats the centre band
		# rather than interpolating it, because interpolation invents colours
		# and would break the palette-exactness every other stage guarantees.
		# The engine has to be told to do the same thing, or the frame that
		# was verified palette-exact stops being it the moment it is resized.
		box.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
		box.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
		if _save(box, "res://resources/ui/%s.tres" % id, id):
			ok += 1
	return ok


# --- ground tiles ------------------------------------------------------------

func _build_tiles(tiles: Dictionary) -> int:
	if tiles.is_empty():
		return 0
	_mkdir("res://resources/tiles")
	var size = tiles["tile_size"]
	var ts := TileSet.new()
	# Isometric, diamond-down, horizontal offset axis: the layout this repo's
	# camera actually produces. tileset.py derives the tile size and both
	# lattice steps from the DimetricCamera basis and proves the tiling with a
	# 3x3 coverage count, so these are read from the manifest rather than
	# guessed at here -- one authority for the geometry, on the Python side.
	ts.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
	ts.tile_layout = TileSet.TILE_LAYOUT_DIAMOND_DOWN
	ts.tile_offset_axis = TileSet.TILE_OFFSET_AXIS_HORIZONTAL
	ts.tile_size = Vector2i(size[0], size[1])

	var n := 0
	for type_name in tiles["tiles"].keys():
		var info = tiles["tiles"][type_name]
		var tex := _load_tex("res://assets/%s" % info["file"], type_name)
		if tex == null:
			continue
		var src := TileSetAtlasSource.new()
		src.texture = tex
		src.texture_region_size = Vector2i(size[0], size[1])
		# One tile per variant, laid out in a row. Variants exist so a floor
		# does not repeat one image on a perfect grid -- the engine picks
		# among them, which is why they belong to a single source rather than
		# being separate tile types.
		for v in range(int(info["variants"])):
			src.create_tile(Vector2i(v, 0))
		ts.add_source(src)
		n += 1

	if n > 0 and not _save(ts, "res://resources/tiles/ground.tres", "tileset"):
		return 0

	# Walls get their own TileSet. Their texture region is 32x112 against a
	# 64x32 grid -- a wall is taller than the cell it stands on -- so they
	# cannot share a source set with the floors.
	#
	# The per-tile draw offset is carried as resource METADATA rather than
	# written into TileData.texture_origin, and that restraint is deliberate.
	# tileset.py's origin_offset is verified: the room is rebuilt from
	# tileset.json alone and required to be pixel-identical to the projected
	# one, and a one-pixel error in it moves 753 pixels. Converting it into
	# texture_origin's own frame is a second, unverified step, because headless
	# Godot has no renderer to check it against. Publishing the verified number
	# and saying it is not yet converted beats publishing a converted number
	# nobody has looked at.
	var walls = tiles.get("walls", {})
	if walls.is_empty():
		return n
	var wts := TileSet.new()
	wts.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
	wts.tile_layout = TileSet.TILE_LAYOUT_DIAMOND_DOWN
	wts.tile_offset_axis = TileSet.TILE_OFFSET_AXIS_HORIZONTAL
	wts.tile_size = Vector2i(size[0], size[1])
	var offsets := {}
	var runs := {}
	for wall_name in walls.keys():
		var info = walls[wall_name]
		var tex := _load_tex("res://assets/%s" % info["file"], wall_name)
		if tex == null:
			continue
		var src := TileSetAtlasSource.new()
		src.texture = tex
		src.texture_region_size = Vector2i(info["tile_size"][0], info["tile_size"][1])
		for v in range(int(info["variants"])):
			src.create_tile(Vector2i(v, 0))
		wts.add_source(src)
		offsets[wall_name] = info["origin_offset"]
		runs[wall_name] = info["run_step"]
		n += 1
	wts.set_meta("origin_offsets", offsets)
	wts.set_meta("run_steps", runs)
	wts.set_meta("stackable", false)   # see tileset.py's WALL_HEIGHT comment
	_save(wts, "res://resources/tiles/walls.tres", "wall tileset")
	return n


# --- bitmap font --------------------------------------------------------------

func _build_font(font: Dictionary) -> int:
	if font.is_empty():
		return 0
	_mkdir("res://resources/font")
	var sizes = font.get("sizes", {})
	var ok := 0
	for cap in sizes.keys():
		var entry = sizes[cap]
		var tex := _load_tex("res://assets/%s" % entry["file"], "font %s" % cap)
		if tex == null:
			continue
		var img := tex.get_image()

		var f := FontFile.new()
		# Fixed size, no hinting, no subpixel positioning, no MSDF. Every one of
		# those exists to make a scalable outline look good at an arbitrary size,
		# and every one of them would blend pixels this pipeline guarantees are
		# palette-exact -- the same reason `bitmap_font._line` has no
		# anti-aliasing.
		f.fixed_size = int(cap)
		f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		f.hinting = TextServer.HINTING_NONE
		f.multichannel_signed_distance_field = false

		var sz := Vector2i(int(cap), 0)
		f.set_texture_image(0, sz, 0, img)
		var cell = entry["cell"]
		var cols := int(entry["columns"])
		var ascent := float(entry["ascent"])
		f.set_cache_ascent(0, int(cap), ascent)
		f.set_cache_descent(0, int(cap), float(entry["descent"]))

		var glyphs = entry["glyphs"]
		for ch in glyphs.keys():
			var g = glyphs[ch]
			var idx := int(g["index"])
			var code: int = ch.unicode_at(0)
			# A space carries an advance and no cell; giving it a zero-size rect
			# is what makes it advance without drawing.
			if idx < 0:
				f.set_glyph_advance(0, int(cap), code, Vector2(float(g["advance"]), 0))
				f.set_glyph_size(0, sz, code, Vector2.ZERO)
				continue
			var rect := Rect2(float((idx % cols) * int(cell[0])),
				float((idx / cols) * int(cell[1])),
				float(cell[0]), float(cell[1]))
			f.set_glyph_texture_idx(0, sz, code, 0)
			f.set_glyph_uv_rect(0, sz, code, rect)
			f.set_glyph_size(0, sz, code, rect.size)
			# Godot places a glyph relative to the BASELINE, and the sheet cell
			# is measured from its top. The offset is therefore minus the
			# ascent, not zero -- get this wrong and every line of text sits one
			# ascent too low, which still renders and still looks like a font.
			f.set_glyph_offset(0, sz, code, Vector2(0.0, -ascent))
			f.set_glyph_advance(0, int(cap), code, Vector2(float(g["advance"]), 0))

		if _save(f, "res://resources/font/font_cap%s.tres" % cap, "font %s" % cap):
			ok += 1
	return ok
