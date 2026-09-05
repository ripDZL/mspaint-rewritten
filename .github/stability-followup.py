from pathlib import Path


def load_text(path: Path):
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), bom


def save_text(path: Path, text: str, bom: bool):
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)


def replace_once(text: str, label: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


path = Path("PaintForm.pas")
text, bom = load_text(path)

edits = [
    (
        "remove duplicate startup history reset",
        """  // Recent
  RecentFiles := TStringList.Create;

  // Reset History
  ResetHistory;

  AppData := GetPathInAppData('Paint', TAppDataType.Roaming, true);""",
        """  // Recent
  RecentFiles := TStringList.Create;

  AppData := GetPathInAppData('Paint', TAppDataType.Roaming, true);""",
    ),
    (
        "properties global lifetime",
        """procedure TMsPaint.SpeedButton17Click(Sender: TObject);
begin
  Properties := TProperties.Create(Self);
  try
    Properties.LoadImageData;
    Properties.ShowModal;
  finally
    Properties.Free;
  end;
end;""",
        """procedure TMsPaint.SpeedButton17Click(Sender: TObject);
begin
  Properties := TProperties.Create(Self);
  try
    Properties.LoadImageData;
    Properties.ShowModal;
  finally
    FreeAndNil(Properties);
  end;
end;""",
    ),
    (
        "selection bitmap ownership",
        """procedure TMsPaint.StealSelectionZone;
var
  I: integer;
  ARect: TRect;
begin
  if SelectionType = TSelectionType.Rectangular then""",
        """procedure TMsPaint.StealSelectionZone;
var
  I: integer;
  ARect: TRect;
begin
  // This routine owns the selection bitmap it creates.
  FreeAndNil(StolenZone);

  if SelectionType = TSelectionType.Rectangular then""",
    ),
    (
        "file paste error handling",
        """procedure TMsPaint.ActionClipboardFileExecute(Sender: TObject);
var
  ABitMap: TBitMap;
begin
  if OpenPictureDialog1.Execute then
    begin
      ABitMap := TBitMap.Create;
      try
        try
          LoadGraphicAsBitmap(OpenPictureDialog1.FileName, ABitMap);

          PastePicture(ABitMap, GetTopmostPoint);
        except

        end;
      finally
        ABitMap.Free;
      end;
    end;
end;""",
        """procedure TMsPaint.ActionClipboardFileExecute(Sender: TObject);
var
  ABitMap: TBitMap;
begin
  if OpenPictureDialog1.Execute then
    begin
      ABitMap := TBitMap.Create;
      try
        try
          LoadGraphicAsBitmap(OpenPictureDialog1.FileName, ABitMap);
          PastePicture(ABitMap, GetTopmostPoint);
        except
          on E: Exception do
            MessageDlg('Paint could not paste the selected image.' + sLineBreak + E.Message,
              mtError, [mbOk], 0);
        end;
      finally
        ABitMap.Free;
      end;
    end;
end;""",
    ),
    (
        "clipboard paste error handling",
        """procedure TMsPaint.ActionPasteClipboardExecute(Sender: TObject);
var
  ABitMap: TBitMap;
begin
  // Load
  ABitMap := TBitMap.Create;
  try
    try
      ABitMap.Assign(Clipboard);

      // Finish Selection
      FinishSelection();

      // Paste
      PastePicture(ABitMap, GetTopmostPoint);
    except

    end;
  finally
    ABitMap.Free;
  end;
end;""",
        """procedure TMsPaint.ActionPasteClipboardExecute(Sender: TObject);
var
  ABitMap: TBitMap;
begin
  // Load
  ABitMap := TBitMap.Create;
  try
    try
      ABitMap.Assign(Clipboard);
      PastePicture(ABitMap, GetTopmostPoint);
    except
      on E: Exception do
        MessageDlg('Paint could not paste the clipboard image.' + sLineBreak + E.Message,
          mtError, [mbOk], 0);
    end;
  finally
    ABitMap.Free;
  end;
end;""",
    ),
    (
        "select all ownership",
        """  SelectionCanvas := DrawBox.ClientRect;
  SelectionImage := Rect(0, 0, Image.Width, Image.Height);
  
  StolenZone := TBitMap.Create;""",
        """  SelectionCanvas := DrawBox.ClientRect;
  SelectionImage := Rect(0, 0, Image.Width, Image.Height);

  FreeAndNil(StolenZone);
  StolenZone := TBitMap.Create;""",
    ),
]

for label, old, new in edits:
    text = replace_once(text, label, old, new)

save_text(path, text, bom)
print(f"Applied {len(edits)} follow-up stability edits.")
