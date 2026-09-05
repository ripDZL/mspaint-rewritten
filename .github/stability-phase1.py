from pathlib import Path


def load_text(path: Path):
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), has_bom


def save_text(path: Path, text: str, has_bom: bool):
    data = text.encode("utf-8")
    if has_bom:
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)


def replace_once(text: str, label: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


path = Path("PaintForm.pas")
text, has_bom = load_text(path)

replacements = [
    (
        "history memory budget constant",
        """const
  LINE_SPACING = 10;
  MAX_UNDO = 50;

  DEFAULT_WIDTH = 1030;""",
        """const
  LINE_SPACING = 10;
  MAX_UNDO = 50;
  MAX_UNDO_MEMORY = UInt64(256) * 1024 * 1024;

  DEFAULT_WIDTH = 1030;""",
    ),
    (
        "save dialog lifetime",
        """  finally
    Save.Free;
  end;
end;

function GetCanvasDPI""",
        """  finally
    FreeAndNil(Save);
  end;
end;

function GetCanvasDPI""",
    ),
    (
        "selection dangling pointer",
        """      // Free
      StolenZone.Free;

      // Update Changed""",
        """      // Free
      FreeAndNil(StolenZone);

      // Update Changed""",
    ),
    (
        "selection flip directions",
        """procedure TMsPaint.FlipHorizonta1Click(Sender: TObject);
begin
  StolenZone.Canvas.StretchDraw(Rect(0, StolenZone.Height, StolenZone.Width, 0), StolenZone);

  UpdateCanvas;
end;

procedure TMsPaint.FlipSelectionSize;
var
  Previous: integer;
begin
  // Selection
  Previous := SelectionCanvas.Width;
  SelectionCanvas.Width := SelectionCanvas.Height;
  SelectionCanvas.Height := Previous;

  // Image
  Previous := SelectionImage.Width;
  SelectionImage.Width := SelectionImage.Height;
  SelectionImage.Height := Previous;
end;

procedure TMsPaint.FlipVertical1Click(Sender: TObject);
begin
  StolenZone.Canvas.StretchDraw(Rect(StolenZone.Width, 0, 0, StolenZone.Height), StolenZone);

  UpdateCanvas;
end;""",
        """procedure TMsPaint.FlipHorizonta1Click(Sender: TObject);
begin
  // Horizontal flip mirrors left/right (the X axis).
  StolenZone.Canvas.StretchDraw(Rect(StolenZone.Width, 0, 0, StolenZone.Height), StolenZone);

  UpdateCanvas;
end;

procedure TMsPaint.FlipSelectionSize;
var
  Previous: integer;
begin
  // Selection
  Previous := SelectionCanvas.Width;
  SelectionCanvas.Width := SelectionCanvas.Height;
  SelectionCanvas.Height := Previous;

  // Image
  Previous := SelectionImage.Width;
  SelectionImage.Width := SelectionImage.Height;
  SelectionImage.Height := Previous;
end;

procedure TMsPaint.FlipVertical1Click(Sender: TObject);
begin
  // Vertical flip mirrors top/bottom (the Y axis).
  StolenZone.Canvas.StretchDraw(Rect(0, StolenZone.Height, StolenZone.Width, 0), StolenZone);

  UpdateCanvas;
end;""",
    ),
    (
        "canvas resize dirty state",
        """      if (AWidth > 0) and (AHeight > 0) then
        begin
          Image.SetSize(AWidth, AHeight);

          // Fill Extended Zones
          with Image.Canvas do
            begin
              Pen.Style := psClear;
              Brush.Style := bsSolid;
              Brush.Color := SecondaryColor;

              ARect := Rect(PrevWidth, 0, AWidth, AHeight);
              FillRect(ARect);

              ARect := Rect(0, PrevHeight, AWidth, AHeight);
              FillRect(ARect);
            end;
        end;""",
        """      if (AWidth > 0) and (AHeight > 0)
        and ((AWidth <> PrevWidth) or (AHeight <> PrevHeight)) then
        begin
          Image.SetSize(AWidth, AHeight);

          // Fill Extended Zones
          with Image.Canvas do
            begin
              Pen.Style := psClear;
              Brush.Style := bsSolid;
              Brush.Color := SecondaryColor;

              ARect := Rect(PrevWidth, 0, AWidth, AHeight);
              FillRect(ARect);

              ARect := Rect(0, PrevHeight, AWidth, AHeight);
              FillRect(ARect);
            end;

          UpdateCanvasDrawn;
        end;""",
    ),
    (
        "font size validation",
        """procedure TMsPaint.Font_SizeExit(Sender: TObject);
begin
  try
    strtoint(Font_Size.Text);
  except
    Font_Size.Text := DrawBox.Font.Size.ToString;
  end;
end;""",
        """procedure TMsPaint.Font_SizeExit(Sender: TObject);
var
  ASize: Integer;
begin
  if not TryStrToInt(Font_Size.Text, ASize) or (ASize <= 0) then
    Font_Size.Text := DrawBox.Font.Size.ToString;
end;""",
    ),
    (
        "transactional file load",
        """procedure TMsPaint.LoadFile;
begin
  LoadGraphicAsBitmap(FileName, Image);

  // Clear any work
  FinishSelection(TCloseMode.Fail);

  // History
  ResetHistory;

  // Status
  FileSaved := true;
  ChangesUnsaved := false;

  // Update
  UpdateFileSize;
  UpdateSizing;
end;""",
        """procedure TMsPaint.LoadFile;
var
  NewImage: TBitmap;
begin
  // Decode into a temporary bitmap first. The current document remains intact
  // if decoding fails or the input file is invalid.
  NewImage := TBitmap.Create;
  try
    LoadGraphicAsBitmap(FileName, NewImage);

    // Clear any transient edit state only after decoding succeeded.
    FinishSelection(TCloseMode.Fail);
    Image.Assign(NewImage);
  finally
    NewImage.Free;
  end;

  // History
  ResetHistory;

  // Status
  FileSaved := true;
  ChangesUnsaved := false;

  // Update
  UpdateFileSize;
  UpdateSizing;
end;""",
    ),
    (
        "safe optional file load",
        """procedure TMsPaint.LoadFileOptional;
var
  I: integer;
begin
  if OpenPictureDialog1.Execute then
    begin
      FileName := OpenPictureDialog1.FileName;

      // Save
      LoadFile;

      // Recent
      I := RecentFiles.IndexOf(FileName);
      if I <> -1 then
        RecentFiles.Delete(I);

      RecentFiles.Add(FileName);

      while RecentFiles.Count > 20 do
        RecentFiles.Delete(0);
    end;
end;""",
        """procedure TMsPaint.LoadFileOptional;
var
  I: Integer;
  PreviousFileName, TargetFileName: string;
begin
  if not OpenPictureDialog1.Execute then
    Exit;

  PreviousFileName := FileName;
  TargetFileName := OpenPictureDialog1.FileName;
  FileName := TargetFileName;

  try
    LoadFile;
  except
    on E: Exception do
      begin
        FileName := PreviousFileName;
        MessageDlg('Paint could not open the selected image.' + sLineBreak + E.Message,
          mtError, [mbOk], 0);
        Exit;
      end;
  end;

  // Recent
  I := RecentFiles.IndexOf(FileName);
  if I <> -1 then
    RecentFiles.Delete(I);

  RecentFiles.Add(FileName);

  while RecentFiles.Count > 20 do
    RecentFiles.Delete(0);
end;""",
    ),
    (
        "new document lifecycle",
        """procedure TMsPaint.NewDocument;
begin
  if Image <> nil then
    Image.Free;
  Image := TBitMap.Create(DEFAULT_WIDTH, DEFAULT_HEIGHT);

  FileName := '';
  FileDisplayName := 'Untitled';

  // Clear
  with Image.Canvas do
    begin
      Brush.Color := clWhite;
      FillRect(ClipRect);
    end;
end;""",
        """procedure TMsPaint.NewDocument;
begin
  // Cancel transient selection state before replacing the backing bitmap.
  FinishSelection(TCloseMode.Fail);
  FreeAndNil(StolenZone);
  FreeAndNil(Image);

  Image := TBitMap.Create;
  Image.PixelFormat := pf32bit;
  Image.SetSize(DEFAULT_WIDTH, DEFAULT_HEIGHT);

  FileName := '';
  FileDisplayName := 'Untitled';
  FileSaved := false;
  ChangesUnsaved := false;

  SelectMode := TSelectionMode.None;
  DrawingPoints := [];
  SetLength(FreeFormBorder, 0, 0);
  SetLength(FreeFormSelection, 0, 0);
  SetLength(FreeFormLines, 0);

  // Clear
  with Image.Canvas do
    begin
      Brush.Style := bsSolid;
      Brush.Color := clWhite;
      FillRect(ClipRect);
    end;

  ResetHistory;
end;""",
    ),
    (
        "paste selection ownership",
        """procedure TMsPaint.PastePicture(Picture: TBitMap; Location: TPoint);
begin
  //
  StolenZone := TBitMap.Create;
  StolenZone.Assign(Picture);

  // Transparent
  ApplyTransparent;

  // UpdateSize
  if Image.Width < StolenZone.Width then
    Image.Width := StolenZone.Width;
  if Image.Height < StolenZone.Height then
    Image.Height := StolenZone.Height;

  UpdateSizing;

  // Get rect
  SelectionImage := Rect(0, 0, StolenZone.Width, StolenZone.Height);
  SelectionImage.Offset(Location);

  // Translate image to canvas selection
  TranslateScale;

  // Select tool 
  SelectTool(SpeedButton13);

  // Set
  SelectMode := TSelectionMode.Exists;

  // Update
  UpdateCanvasDrawn;
end;""",
        """procedure TMsPaint.PastePicture(Picture: TBitMap; Location: TPoint);
var
  NewWidth, NewHeight: Integer;
  ResizedImage: TBitmap;
begin
  // Finish the previous selection before replacing StolenZone.
  FinishSelection;
  SelectTool(SpeedButton13);
  FreeAndNil(StolenZone);

  StolenZone := TBitMap.Create;
  StolenZone.Assign(Picture);

  // Transparent
  ApplyTransparent;

  // Grow the canvas when the pasted selection would extend past its edge.
  NewWidth := Max(Image.Width, Location.X + StolenZone.Width);
  NewHeight := Max(Image.Height, Location.Y + StolenZone.Height);
  if (NewWidth <> Image.Width) or (NewHeight <> Image.Height) then
    begin
      ResizedImage := TBitmap.Create;
      try
        ResizedImage.PixelFormat := Image.PixelFormat;
        ResizedImage.SetSize(NewWidth, NewHeight);
        ResizedImage.Canvas.Brush.Style := bsSolid;
        ResizedImage.Canvas.Brush.Color := SecondaryColor;
        ResizedImage.Canvas.FillRect(ResizedImage.Canvas.ClipRect);
        ResizedImage.Canvas.Draw(0, 0, Image);
        Image.Assign(ResizedImage);
      finally
        ResizedImage.Free;
      end;
    end;

  UpdateSizing;

  // Get rect
  SelectionImage := Rect(0, 0, StolenZone.Width, StolenZone.Height);
  SelectionImage.Offset(Location);

  // Translate image to canvas selection
  TranslateScale;

  // Set
  SelectMode := TSelectionMode.Exists;

  // Pasting is already a document change, but the final bitmap snapshot is
  // created when the selection is committed. This keeps Undo one-step sane.
  ChangesUnsaved := true;
  UpdateCanvas;
end;""",
    ),
    (
        "text width comparison",
        """              if SelectionImage.Height < AWidth then
                begin
                  SelectionImage.Width := AWidth;""",
        """              if SelectionImage.Width < AWidth then
                begin
                  SelectionImage.Width := AWidth;""",
    ),
    (
        "GDI brush and pen ownership",
        """            2: begin
              ARect := TRect.Create(PositionImage);
              ARect.Inflate(BrushSize div 2, BrushSize div 2);
              
              GDICircle(ARect, GetRGB(DrawColor, 100).MakeGDIBrush, nil);
            end;
            3: begin
              GDILine(MakeLine(PReviousImage, PositionImage), GetRGB(DrawColor, 200).MakeGDIPen(BrushSize));
            end;""",
        """            2: begin
              ARect := TRect.Create(PositionImage);
              ARect.Inflate(BrushSize div 2, BrushSize div 2);

              var ABrush := GetRGB(DrawColor, 100).MakeGDIBrush;
              try
                GDICircle(ARect, ABrush, nil);
              finally
                ABrush.Free;
              end;
            end;
            3: begin
              var APen := GetRGB(DrawColor, 200).MakeGDIPen(BrushSize);
              try
                GDILine(MakeLine(PreviousImage, PositionImage), APen);
              finally
                APen.Free;
              end;
            end;""",
    ),
    (
        "selection overlay bitmap lifetime",
        """                  with TBitMap.Create do
                    begin
                      SetSize(SelectionCanvas.Width, SelectionCanvas.Height);

                      with Canvas do
                        begin
                          Brush.Color := clBlack;
                          FillRect(ClipRect);

                          if SelectMode = TSelectionMode.Creating then
                            Pen.Color := clWhite
                          else
                            Pen.Color := InvertColor(ColorToRGB(clHighlight));
                          Pen.Style := psDash;

                          Brush.Style := bsClear;
                          Rectangle(Canvas.ClipRect);
                        end;

                      StretchInvertedMask(Canvas, DrawBox.Canvas, SelectionCanvas);
                    end;""",
        """                  with TBitMap.Create do
                  try
                    SetSize(SelectionCanvas.Width, SelectionCanvas.Height);

                    with Canvas do
                      begin
                        Brush.Color := clBlack;
                        FillRect(ClipRect);

                        if SelectMode = TSelectionMode.Creating then
                          Pen.Color := clWhite
                        else
                          Pen.Color := InvertColor(ColorToRGB(clHighlight));
                        Pen.Style := psDash;

                        Brush.Style := bsClear;
                        Rectangle(Canvas.ClipRect);
                      end;

                    StretchInvertedMask(Canvas, DrawBox.Canvas, SelectionCanvas);
                  finally
                    Free;
                  end;""",
    ),
    (
        "freeform overlay bitmap lifetime",
        """                  with TBitMap.Create do
                    begin
                      SetSize(DrawBox.Width, DrawBox.Height);

                      with Canvas do
                        begin
                          Brush.Color := clBlack;
                          FillRect(ClipRect);
                          Pen.Color := clWhite;

                          for AX := 0 to High(FreeFormBorder) do
                            for AY := 0 to High(FreeFormBorder[AX]) do
                              if FreeFormBorder[AX, AY] then
                                Pixels[round(AX * Scale), round(AY * Scale)] := clWhite;
                        end;

                      StretchInvertedMask(Canvas, DrawBox.Canvas, DrawBox.ClientRect);
                    end;""",
        """                  with TBitMap.Create do
                  try
                    SetSize(DrawBox.Width, DrawBox.Height);

                    with Canvas do
                      begin
                        Brush.Color := clBlack;
                        FillRect(ClipRect);
                        Pen.Color := clWhite;

                        for AX := 0 to High(FreeFormBorder) do
                          for AY := 0 to High(FreeFormBorder[AX]) do
                            if FreeFormBorder[AX, AY] then
                              Pixels[round(AX * Scale), round(AY * Scale)] := clWhite;
                      end;

                    StretchInvertedMask(Canvas, DrawBox.Canvas, DrawBox.ClientRect);
                  finally
                    Free;
                  end;""",
    ),
    (
        "zoom overlay bitmap lifetime",
        """          with TBitMap.Create do
            begin
              SetSize(ZoomRect.Width, ZoomRect.Height);

              with Canvas do
                begin
                  Brush.Color := clBlack;
                  FillRect(ClipRect);
                  Pen.Color := clWhite;
                  Pen.Width := 2;

                  ARect := ClipRect;
                  ARect.Inflate(-1, -1, 0, 0);

                  Brush.Style := bsClear;
                  Rectangle(ARect);
                end;

              StretchInvertedMask(Canvas, DrawBox.Canvas, ZoomRect);
            end;""",
        """          with TBitMap.Create do
          try
            SetSize(ZoomRect.Width, ZoomRect.Height);

            with Canvas do
              begin
                Brush.Color := clBlack;
                FillRect(ClipRect);
                Pen.Color := clWhite;
                Pen.Width := 2;

                ARect := ClipRect;
                ARect.Inflate(-1, -1, 0, 0);

                Brush.Style := bsClear;
                Rectangle(ARect);
              end;

            StretchInvertedMask(Canvas, DrawBox.Canvas, ZoomRect);
          finally
            Free;
          end;""",
    ),
    (
        "resize overlay bitmap lifetime",
        """  if SizePreview.Enabled then
    begin
      DrawBox.Canvas.TextOut(10, 10, 'drawin');
      with TBitMap.Create do
        begin
          SetSize(DotsSize.Width-4, DotsSize.Height-4);

          with Canvas do
            begin
              Brush.Color := clBlack;
              FillRect(ClipRect);
              Pen.Color := clWhite;
              Pen.Width := 1;
              Pen.Style := psDot;

              ARect := ClipRect;
              ARect.Inflate(1, 1, 0, 0);

              Brush.Style := bsClear;
              Rectangle(ARect);
            end;

          StretchInvertedMask(Canvas, DrawBox.Canvas, DotsSize.ClientRect);
        end;
    end;""",
        """  if SizePreview.Enabled then
    begin
      with TBitMap.Create do
      try
        SetSize(DotsSize.Width-4, DotsSize.Height-4);

        with Canvas do
          begin
            Brush.Color := clBlack;
            FillRect(ClipRect);
            Pen.Color := clWhite;
            Pen.Width := 1;
            Pen.Style := psDot;

            ARect := ClipRect;
            ARect.Inflate(1, 1, 0, 0);

            Brush.Style := bsClear;
            Rectangle(ARect);
          end;

        StretchInvertedMask(Canvas, DrawBox.Canvas, DotsSize.ClientRect);
      finally
        Free;
      end;
    end;""",
    ),
    (
        "linear grid rendering",
        """        AX := DrawBox.Width div LINE_SPACING;
        AY := DrawBox.Height div LINE_SPACING;

        for I := 0 to AX do
          for J := 0 to AY do
            begin
              MoveTo(I * LINE_SPACING, J * LINE_SPACING);
              LineTo((I+1) * LINE_SPACING, (J) * LINE_SPACING);

              MoveTo(I * LINE_SPACING, J * LINE_SPACING);
              LineTo((I) * LINE_SPACING, (J+1) * LINE_SPACING);
            end;""",
        """        AX := DrawBox.Width div LINE_SPACING;
        AY := DrawBox.Height div LINE_SPACING;

        // Draw each grid line once. The previous nested loop redrew the same
        // segments O(X*Y) times as the viewport grew.
        for I := 0 to AX do
          begin
            MoveTo(I * LINE_SPACING, 0);
            LineTo(I * LINE_SPACING, DrawBox.Height);
          end;

        for J := 0 to AY do
          begin
            MoveTo(0, J * LINE_SPACING);
            LineTo(DrawBox.Width, J * LINE_SPACING);
          end;""",
    ),
    (
        "save codec validation",
        """procedure TMsPaint.SaveFile;
var
  ImageType: TImageType;
  Ext: string;

  G: TGraphic;
begin
  // Image Type
  ImageType := TImageType.Bitmap;

  Ext := AnsiLowerCase(ExtractFileExt(FileName));
  if Ext = '.png' then
    ImageType := TImageType.PNG
  else
  if (Ext = '.jpeg') or (Ext = '.jpg') then
    ImageType := TImageType.Jpeg
  else
  if Ext = '.gif' then
    ImageType := TImageType.Gif;
  
  // Save
  case ImageType of
    TImageType.PNG: G := TPngImage.Create;
    TImageType.Jpeg: G := TJpegImage.Create;
    TImageType.Gif: G := TGifImage.Create;
    else G := TBitMap.Create; 
  end;
  
  try
    G.Assign(Image);
    G.SaveToFile(FileName);
  finally
    G.Free;
  end;

  // Status
  FileSaved := true;
  ChangesUnsaved := false;

  // Update
  UpdateFileSize;
  UpdateSizing;
end;""",
        """procedure TMsPaint.SaveFile;
var
  ImageType: TImageType;
  Ext: string;
  G: TGraphic;
begin
  if FileName = '' then
    raise EInOutError.Create('No destination file name was specified.');

  // Image Type
  Ext := AnsiLowerCase(ExtractFileExt(FileName));
  if Ext = '.png' then
    ImageType := TImageType.PNG
  else if (Ext = '.jpeg') or (Ext = '.jpg') then
    ImageType := TImageType.Jpeg
  else if Ext = '.gif' then
    ImageType := TImageType.Gif
  else if Ext = '.bmp' then
    ImageType := TImageType.Bitmap
  else if Ext = '.ico' then
    raise EInvalidGraphic.Create('Saving ICO files is not supported yet.')
  else
    raise EInvalidGraphic.CreateFmt('Unsupported output format: %s', [Ext]);

  // Save
  case ImageType of
    TImageType.PNG: G := TPngImage.Create;
    TImageType.Jpeg: G := TJpegImage.Create;
    TImageType.Gif: G := TGifImage.Create;
    else G := TBitMap.Create;
  end;

  try
    G.Assign(Image);
    G.SaveToFile(FileName);
  finally
    G.Free;
  end;

  // Status changes only after the encoder completed successfully.
  FileSaved := true;
  ChangesUnsaved := false;

  // Update
  UpdateFileSize;
  UpdateSizing;
end;""",
    ),
    (
        "save as result and rollback",
        """function TMsPaint.SaveFileOptional(SaveAs: boolean): boolean;
var
  Ext: string;
  I: integer;
begin
  Result := false;

  // Finish editing
  FinishSelection();

  // Save
  if FileSaved and (FileName <> '') and not SaveAs then begin
    SaveFile;

    Result := true;
    Exit;
  end;

  // Save As...
  if not SavePictureDialog1.Execute then
    Exit;

  // Set
  FileName := SavePictureDialog1.FileName;

  // Extension
  if ExtractFileExt(FileName) = '' then
    begin
      case SavePictureDialog1.FilterIndex of
        1: Ext := 'png';
        2: Ext := 'jpeg';
        3: Ext := 'bmp';
        4: Ext := 'gif';
        5: Ext := 'ico';
      end;

      FileName := FileName + '.' + Ext;
    end;

  // Add to recents
  I := RecentFiles.IndexOf(FileName);
  if I <> -1 then
    RecentFiles.Delete(I);

  RecentFiles.Add(FileName);

  // Save
  SaveFile;
end;""",
        """function TMsPaint.SaveFileOptional(SaveAs: boolean): boolean;
var
  Ext: string;
  I: Integer;
  PreviousFileName, TargetFileName: string;
begin
  Result := false;

  // Finish editing
  FinishSelection();

  // Save
  if FileSaved and (FileName <> '') and not SaveAs then
    begin
      try
        SaveFile;
        Result := true;
      except
        on E: Exception do
          MessageDlg('Paint could not save the image.' + sLineBreak + E.Message,
            mtError, [mbOk], 0);
      end;
      Exit;
    end;

  // Save As...
  if not SavePictureDialog1.Execute then
    Exit;

  TargetFileName := SavePictureDialog1.FileName;

  // Extension
  if ExtractFileExt(TargetFileName) = '' then
    begin
      case SavePictureDialog1.FilterIndex of
        1: Ext := 'png';
        2: Ext := 'jpeg';
        3: Ext := 'bmp';
        4: Ext := 'gif';
        5: begin
          MessageDlg('Saving ICO files is not supported yet.', mtWarning, [mbOk], 0);
          Exit;
        end;
      else
        Ext := 'png';
      end;

      TargetFileName := TargetFileName + '.' + Ext;
    end;

  if SameText(ExtractFileExt(TargetFileName), '.ico') then
    begin
      MessageDlg('Saving ICO files is not supported yet.', mtWarning, [mbOk], 0);
      Exit;
    end;

  PreviousFileName := FileName;
  FileName := TargetFileName;
  try
    SaveFile;
  except
    on E: Exception do
      begin
        FileName := PreviousFileName;
        MessageDlg('Paint could not save the image.' + sLineBreak + E.Message,
          mtError, [mbOk], 0);
        Exit;
      end;
  end;

  // Add to recents only after the save succeeds.
  I := RecentFiles.IndexOf(FileName);
  if I <> -1 then
    RecentFiles.Delete(I);

  RecentFiles.Add(FileName);
  while RecentFiles.Count > 20 do
    RecentFiles.Delete(0);

  Result := true;
end;""",
    ),
    (
        "rotation participates in history",
        """  // Panel
  HideMiniPanels;

  // Update
  UpdateSizing;
end;

procedure TMsPaint.SelectBrush""",
        """  // Panel
  HideMiniPanels;

  // Update
  UpdateCanvasDrawn;
  UpdateSizing;
end;

procedure TMsPaint.SelectBrush""",
    ),
    (
        "thumbnail picture ownership",
        """  Thumbnail.Preview.Picture.Assign(Image);

  Thumbnail.Preview.Picture.Graphic := Image;
  Thumbnail.Show;""",
        """  Thumbnail.Preview.Picture.Assign(Image);
  Thumbnail.Show;""",
    ),
    (
        "history reset position",
        """  SetLength(History, 0);
  
  CacheNew;
end;

function TMsPaint.ReverseScale""",
        """  SetLength(History, 0);
  DoPos := 0;

  CacheNew;
end;

function TMsPaint.ReverseScale""",
    ),
    (
        "history load dirty state",
        """procedure TMsPaint.LoadHistory(Position: integer);
begin
  Image.Assign(History[Position]);
  DoPos := Position;

  UpdateSizing;
end;""",
        """procedure TMsPaint.LoadHistory(Position: integer);
begin
  Image.Assign(History[Position]);
  DoPos := Position;

  // Undo/redo changes the document relative to the last explicit save.
  ChangesUnsaved := true;
  UpdateSizing;
end;""",
    ),
    (
        "memory bounded history",
        """procedure TMsPaint.CacheNew;
var
  I: Integer;
begin
  if DoPos > 0 then
    begin
      for I := 0 to High(History)-DoPos do
        History[I] := History[I+DoPos];

      SetLength( History, Length(History)-DoPos );

      DoPos := 0;
    end;

  // Move
  SetLength(History, Length(History)+1);
  for I := High(History) downto 1 do
    History[I] := History[I-1];

  // Add
  History[0] := TBitMap.Create;
  with History[0] do
    History[0].Assign(Image);

  // Limit
  if Length(History) > MAX_UNDO then
    SetLength(History, MAX_UNDO);
end;""",
        """procedure TMsPaint.CacheNew;
var
  I, MaxEntries: Integer;
  BitmapBytes: UInt64;
begin
  // If the user edited after Undo, discard and free the redo branch first.
  if DoPos > 0 then
    begin
      for I := 0 to DoPos - 1 do
        History[I].Free;

      for I := DoPos to High(History) do
        History[I-DoPos] := History[I];

      SetLength(History, Length(History)-DoPos);
      DoPos := 0;
    end;

  // Move
  SetLength(History, Length(History)+1);
  for I := High(History) downto 1 do
    History[I] := History[I-1];

  // Add
  History[0] := TBitMap.Create;
  History[0].Assign(Image);

  // Limit history by count and by approximate raw bitmap memory. Large 4K+
  // documents therefore cannot silently consume gigabytes of RAM.
  BitmapBytes := UInt64(Max(Image.Width, 1)) * UInt64(Max(Image.Height, 1)) * 4;
  MaxEntries := Integer(MAX_UNDO_MEMORY div BitmapBytes);
  MaxEntries := EnsureRange(MaxEntries, 2, MAX_UNDO);

  if Length(History) > MaxEntries then
    begin
      for I := MaxEntries to High(History) do
        History[I].Free;
      SetLength(History, MaxEntries);
    end;
end;""",
    ),
    (
        "font styling parse safety",
        """procedure TMsPaint.ApplyFontStyling(Font: TFont);
begin
  Font.Color := PrimaryColor;
  Font.Name := Font_List.Text;
  Font.Size := strtoint(Font_Size.Text);

  Font.Style := [];""",
        """procedure TMsPaint.ApplyFontStyling(Font: TFont);
var
  ASize: Integer;
begin
  Font.Color := PrimaryColor;
  Font.Name := Font_List.Text;

  if not TryStrToInt(Font_Size.Text, ASize) or (ASize <= 0) then
    ASize := 11;
  Font.Size := EnsureRange(ASize, 1, 512);

  Font.Style := [];""",
    ),
    (
        "untitled file size display",
        """procedure TMsPaint.UpdateFileSize;
begin
  FileDisplayName := ExtractFileName(FileName);

  Label12.Show;
  Label13.Caption := 'Size: ' + GetFileSizeInStr( FileName );
end;""",
        """procedure TMsPaint.UpdateFileSize;
begin
  if FileName = '' then
    begin
      FileDisplayName := 'Untitled';
      Label12.Hide;
      Label13.Caption := '';
      Exit;
    end;

  FileDisplayName := ExtractFileName(FileName);
  Label12.Show;

  if TFile.Exists(FileName) then
    Label13.Caption := 'Size: ' + GetFileSizeInStr(FileName)
  else
    Label13.Caption := '';
end;""",
    ),
    (
        "drop handle lifetime and safe save action",
        """procedure TMsPaint.WMDropFiles(var Msg: TWMDropFiles);
var
  Catcher: TFileCatcher;
begin
  Catcher := TFileCatcher.Create(Msg.Drop);
  if Catcher.FileCount < 1 then
    Exit;

  // Load
  if not CheckSavedCanProceed or not TFile.Exists(Catcher.Files[0]) then
    Exit;

  FileName := Catcher.Files[0];
  MsPaint.LoadFile;
  MsPaint.UpdateSizing;
end;

procedure TMsPaint.SaveActionExecute(Sender: TObject);
begin
  SaveFile;
end;""",
        """procedure TMsPaint.WMDropFiles(var Msg: TWMDropFiles);
var
  Catcher: TFileCatcher;
  I: Integer;
  PreviousFileName, DroppedFile: string;
begin
  Catcher := TFileCatcher.Create(Msg.Drop);
  try
    if Catcher.FileCount < 1 then
      Exit;

    DroppedFile := Catcher.Files[0];
    if not TFile.Exists(DroppedFile) or not CheckSavedCanProceed then
      Exit;

    PreviousFileName := FileName;
    FileName := DroppedFile;
    try
      LoadFile;
    except
      on E: Exception do
        begin
          FileName := PreviousFileName;
          MessageDlg('Paint could not open the dropped image.' + sLineBreak + E.Message,
            mtError, [mbOk], 0);
          Exit;
        end;
    end;

    I := RecentFiles.IndexOf(FileName);
    if I <> -1 then
      RecentFiles.Delete(I);
    RecentFiles.Add(FileName);
    while RecentFiles.Count > 20 do
      RecentFiles.Delete(0);
  finally
    Catcher.Free;
  end;
end;

procedure TMsPaint.SaveActionExecute(Sender: TObject);
begin
  SaveFileOptional;
end;""",
    ),
]

for label, old, new in replacements:
    text = replace_once(text, label, old, new)

# Add deterministic finalization cleanup for manually owned global objects.
old_tail = """procedure TMsPaint.ClickPB(Sender: TObject);
begin
  SelectedTop := TPaintBox(Sender).Tag;

  SelectPanel(SelectedTop);

  // Redraw All
  Panel1.Repaint;
  PaintBox5.Repaint;
end;

end."""
new_tail = """procedure TMsPaint.ClickPB(Sender: TObject);
begin
  SelectedTop := TPaintBox(Sender).Tag;

  SelectPanel(SelectedTop);

  // Redraw All
  Panel1.Repaint;
  PaintBox5.Repaint;
end;

procedure FreeGlobalPaintResources;
var
  I: Integer;
begin
  for I := 0 to High(History) do
    History[I].Free;
  SetLength(History, 0);

  FreeAndNil(StolenZone);
  FreeAndNil(Image);
  FreeAndNil(RecentFiles);
end;

finalization
  FreeGlobalPaintResources;

end."""
text = replace_once(text, "global resource finalization", old_tail, new_tail)

save_text(path, text, has_bom)

# Remove a developer-machine-only debugger argument from the project file.
dproj = Path("Paint.dproj")
dproj_text, dproj_bom = load_text(dproj)
dproj_text = replace_once(
    dproj_text,
    "developer debugger path",
    "        <Debugger_RunParams>&quot;C:\\Users\\Codrut\\Downloads\\test.png&quot;</Debugger_RunParams>\n",
    "",
)
save_text(dproj, dproj_text, dproj_bom)

print(f"Applied {len(replacements) + 2} asserted stability edits successfully.")
