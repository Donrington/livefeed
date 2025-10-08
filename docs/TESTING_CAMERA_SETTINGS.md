# Testing Camera Settings

## How to Test

1. **Start the Pi publisher** (if not running)
2. **Start Django server**: `python manage.py runserver`
3. **Open browser** to `http://localhost:9000/settings/`
4. **Click Camera tab**
5. **Move the sliders**:
   - Brightness (-130 to 130)
   - Contrast (-130 to 130)
   - Exposure (-130 to 0)
   - Focus (0 to 500)

## Expected Behavior

### When You Move a Slider:
- ✅ The value updates immediately in the label
- ✅ Console shows: `📤 Sent brightness = 50`
- ✅ Pi terminal shows: `Updated brightness to 50`
- ✅ Pi terminal shows: `Applied setting: brightness = 50.0`
- ✅ Camera adjusts in real-time (you'll see brightness change on video)
- ✅ No Blob errors in console

### When You Navigate Away and Back:
- ✅ Settings remain applied to camera
- ✅ Sliders sync to current values (not defaults)
- ✅ Camera settings persist

### In the Browser Console:
You should see:
```
⚙️ Settings initialized
✅ Settings WebSocket connected
📤 Sent brightness = 50
```

You should NOT see:
```
❌ Error parsing WebSocket message: SyntaxError... Blob...
```

## What Was Fixed

### Fix #1: Blob Error
- **Problem**: Django sent binary protobuf to browser
- **Solution**: Consumer now tracks Pi vs browser connections and routes messages correctly

### Fix #2: Settings Not Syncing
- **Problem**: Sliders reset to defaults when navigating
- **Solution**: Pi now sends camera settings on every frame, so frontend stays in sync

## Persistence Notes

**During Session:** Settings are stored in Pi's memory and persist across page navigation.

**After Restart:** Settings reset to defaults when you restart the Pi publisher.

**For Permanent Storage:** Would need to add database or config file to save settings between restarts.

## Troubleshooting

### If sliders don't update when you return:
- Check browser console for WebSocket connection
- Check Pi terminal for status messages being sent

### If camera doesn't adjust:
- Check Pi terminal for "Applied setting" messages
- Check Pi terminal for error messages
- Verify camera supports the property (some webcams don't support all properties)

### If you see Blob errors:
- Make sure Django server was restarted after the fix
- Clear browser cache
- Check that `consumers.py` has the latest code
