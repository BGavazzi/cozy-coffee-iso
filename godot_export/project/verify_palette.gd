extends SceneTree

# Reads back the two facts the palette LUT depends on: that canvas textures
# default to nearest, and that the staged texture is the size and content the
# build manifest claims. Godot headless has no renderer, so this checks the
# setting and the pixels -- not a drawn frame.
func _init():
    var f := int(ProjectSettings.get_setting(
        "rendering/textures/canvas_textures/default_texture_filter", 1))
    var img := (load("res://assets/palette/lut.png") as Texture2D).get_image()
    var manifest: Dictionary = JSON.parse_string(
        FileAccess.get_file_as_string("res://build_manifest.json"))
    var pal: Dictionary = manifest["palettes"]
    var rows := []
    for name in pal["rows"]:
        var y: int = pal["rows"][name]
        var row := []
        for x in range(img.get_width()):
            var c := img.get_pixel(x, y)
            row.append("#%02x%02x%02x" % [
                int(round(c.r * 255.0)), int(round(c.g * 255.0)),
                int(round(c.b * 255.0))])
        rows.append({"name": name, "row": y, "colours": row})
    print("VERIFY_LUT_JSON:" + JSON.stringify({
        "filter": f,
        "size": [img.get_width(), img.get_height()],
        "rows": rows,
    }))
    quit()
