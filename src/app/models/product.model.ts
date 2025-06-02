export type Scores = {
  [category: string]: {
    [metric: string]: (number | null)[][];
  };
};

export type Details = {
  [key: string]: string | number | null;
};

export interface Product {
  id: string;
  store: string;
  name: string;
  images: string[];
  scores: Scores;
  details: Details;
}
