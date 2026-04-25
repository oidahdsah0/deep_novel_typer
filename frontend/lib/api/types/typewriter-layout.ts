export type TypewriterLayoutSettings = {
  first_line_indent_chars: number;
  font_size_px: number;
  paragraph_gap_lines: number;
  line_height_multiplier: number;
  updated_at: string | null;
};

export type TypewriterLayoutSettingsInput = {
  first_line_indent_chars: number;
  font_size_px: number;
  paragraph_gap_lines: number;
  line_height_multiplier: number;
};
