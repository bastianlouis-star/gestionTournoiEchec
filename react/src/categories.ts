export type Category = 'junior' | 'senior' | 'veteran'

export const CATEGORIES: { value: Category, label: string, color: string }[] = [
    { value: 'junior', label: 'Junior', color: '#1f7a6d' },
    { value: 'senior', label: 'Senior', color: '#2f5d8c' },
    { value: 'veteran', label: 'Vétéran', color: '#7a3b72' },
]

export const CATEGORY_BY_VALUE = Object.fromEntries(
    CATEGORIES.map((category) => [category.value, category])
) as Record<Category, typeof CATEGORIES[number]>
