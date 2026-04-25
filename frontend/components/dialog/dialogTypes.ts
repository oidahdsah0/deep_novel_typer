export type DialogTone = "default" | "danger";

export type ConfirmOptions = {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: DialogTone;
};

export type PromptOptions = {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  placeholder?: string;
};

export type NoticeOptions = {
  title?: string;
  closeLabel?: string;
};

export type ConfirmRequest = {
  id: number;
  kind: "confirm";
  message: string;
  options: ConfirmOptions;
  resolve: (value: boolean) => void;
};

export type PromptRequest = {
  id: number;
  kind: "prompt";
  message: string;
  defaultValue: string;
  options: PromptOptions;
  resolve: (value: string | null) => void;
};

export type NoticeRequest = {
  id: number;
  kind: "notice";
  message: string;
  options: NoticeOptions;
  resolve: () => void;
};

export type DialogRequest = ConfirmRequest | PromptRequest | NoticeRequest;
export type DialogRequestInput =
  | Omit<ConfirmRequest, "id">
  | Omit<PromptRequest, "id">
  | Omit<NoticeRequest, "id">;

export type DialogApi = {
  confirm: (message: string, options?: ConfirmOptions) => Promise<boolean>;
  prompt: (
    message: string,
    defaultValue?: string,
    options?: PromptOptions,
  ) => Promise<string | null>;
  notice: (message: string, options?: NoticeOptions) => Promise<void>;
};

export type DialogConfirm = DialogApi["confirm"];
export type DialogNotice = DialogApi["notice"];
export type DialogPrompt = DialogApi["prompt"];
