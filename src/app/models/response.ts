export type K9Response<T> = {
  status: number;
  body: T | null;
  error?: string | null;
};
