unit PropertiesForm;

interface

uses
  Winapi.Windows, Winapi.Messages, System.SysUtils, System.Variants, System.Classes, Vcl.Graphics,
  Vcl.Controls, Vcl.Forms, Vcl.Dialogs, Vcl.ExtCtrls, Vcl.StdCtrls, IOUtils,
  Cod.Files, UITypes;

type
  TProperties = class(TForm)
    Button1: TButton;
    Button2: TButton;
    Panel1: TPanel;
    GroupBox1: TGroupBox;
    Label1: TLabel;
    Label2: TLabel;
    Label3: TLabel;
    Label4: TLabel;
    Label5: TLabel;
    Label6: TLabel;
    GroupBox2: TGroupBox;
    RadioButton1: TRadioButton;
    RadioButton2: TRadioButton;
    RadioButton3: TRadioButton;
    GroupBox3: TGroupBox;
    RadioButton4: TRadioButton;
    Label7: TLabel;
    Edit1: TEdit;
    Label8: TLabel;
    Edit2: TEdit;
    Button3: TButton;
    procedure Button3Click(Sender: TObject);
    procedure Button1Click(Sender: TObject);
    procedure ValidateValues(Sender: TObject);
  private
    { Private declarations }
  public
    { Public declarations }
    procedure LoadImageData;
  end;

var
  Properties: TProperties;

implementation

uses
  PaintForm;

{$R *.dfm}

const
  MAX_CANVAS_DIMENSION = 32767;
  MAX_CANVAS_PIXELS = UInt64(64) * 1024 * 1024;

function ValidCanvasSize(const W, H: Integer): Boolean;
begin
  Result := (W > 0) and (H > 0)
    and (W <= MAX_CANVAS_DIMENSION)
    and (H <= MAX_CANVAS_DIMENSION)
    and (UInt64(W) * UInt64(H) <= MAX_CANVAS_PIXELS);
end;

procedure TProperties.Button1Click(Sender: TObject);
var
  W, H: Integer;
  NewImage: TBitmap;
begin
  if not TryStrToInt(Edit1.Text, W) or not TryStrToInt(Edit2.Text, H)
    or not ValidCanvasSize(W, H) then
  begin
    MessageDlg(
      'Please enter a valid canvas size. Width and height must be positive, '
      + 'no larger than 32767 pixels, and the total canvas must not exceed 64 megapixels.',
      mtWarning, [mbOk], 0);
    Exit;
  end;

  if RadioButton1.Checked then
    Units := TUnit.Inch
  else if RadioButton2.Checked then
    Units := TUnit.Cm
  else if RadioButton3.Checked then
    Units := TUnit.Pixel;

  if (Image.Width <> W) or (Image.Height <> H) then
  begin
    NewImage := TBitmap.Create;
    try
      NewImage.PixelFormat := Image.PixelFormat;
      NewImage.SetSize(W, H);

      // Match the normal canvas-resize behavior: newly exposed space uses Color 2.
      NewImage.Canvas.Brush.Style := bsSolid;
      NewImage.Canvas.Brush.Color := SecondaryColor;
      NewImage.Canvas.FillRect(NewImage.Canvas.ClipRect);
      NewImage.Canvas.Draw(0, 0, Image);

      Image.Assign(NewImage);
    finally
      NewImage.Free;
    end;

    // A properties resize is a document edit and must participate in undo/save state.
    MsPaint.UpdateCanvasDrawn;
  end;

  MsPaint.UpdateSizing;
end;

procedure TProperties.Button3Click(Sender: TObject);
begin
  Edit1.Text := DEFAULT_WIDTH.ToString;
  Edit2.Text := DEFAULT_HEIGHT.ToString;
end;

procedure TProperties.LoadImageData;
begin
  // Image
  if TFile.Exists(FileName) then
    begin
      Label2.Caption := DateTimeToStr(TFile.GetLastWriteTime(FileName));
      Label4.Caption := GetFileSizeInStr(FileName);
    end
  else
    begin
      Label2.Caption := 'Not Available';
      Label4.Caption := 'Not Available';
    end;

  Label6.Caption := GetCanvasDPI(Image.Canvas).ToString + ' DPI';

  // Size
  Edit1.Text := Image.Width.ToString;
  Edit2.Text := Image.Height.ToString;

  // Unit
  case Units of
    TUnit.Pixel: RadioButton3.Checked := true;
    TUnit.Cm: RadioButton2.Checked := true;
    TUnit.Inch: RadioButton1.Checked := true;
  end;
end;

procedure TProperties.ValidateValues(Sender: TObject);
var
  W, H: Integer;
begin
  Button1.Enabled := TryStrToInt(Edit1.Text, W)
    and TryStrToInt(Edit2.Text, H)
    and ValidCanvasSize(W, H);
end;

end.
