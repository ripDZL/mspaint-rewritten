unit ThumbnailForm;

interface

uses
  Winapi.Windows, Winapi.Messages, System.SysUtils, System.Variants, System.Classes, Vcl.Graphics,
  Vcl.Controls, Vcl.Forms, Vcl.Dialogs, Cod.Visual.Image;

type
  TThumbnail = class(TForm)
    Preview: CImage;
    procedure FormClose(Sender: TObject; var Action: TCloseAction);
  private
    { Private declarations }
  public
    { Public declarations }
  end;

var
  Thumbnail: TThumbnail;

implementation

{$R *.dfm}

procedure TThumbnail.FormClose(Sender: TObject; var Action: TCloseAction);
begin
  // Let VCL finish dispatching OnClose before the form is destroyed.
  Thumbnail := nil;
  Action := caFree;
end;

end.
