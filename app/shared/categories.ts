// Единый справочник категорий для TypeScript (мини-приложение).
// Значения обязаны совпадать 1-в-1 с shared/categories.py.
// Изменения — по согласованию со всей командой (антон + дима + женя + олежа).

export const CATEGORY_SLUGS = [
  "concert",
  "exhibition",
  "theater",
  "lecture",
  "master_class",
  "festival",
  "cinema",
  "children",
] as const;

export type CategorySlug = (typeof CATEGORY_SLUGS)[number];

export const CATEGORY_NAMES: Record<CategorySlug, string> = {
  concert: "Концерт",
  exhibition: "Выставка",
  theater: "Театр",
  lecture: "Лекция",
  master_class: "Мастер-класс",
  festival: "Фестиваль",
  cinema: "Кино",
  children: "Детям",
};

export function categoryName(slug: string): string {
  return (CATEGORY_NAMES as Record<string, string>)[slug] ?? slug;
}
