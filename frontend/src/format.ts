const map: Record<string, string> = {
  live: 'Реальный',
  paper: 'Бумажный',
  historical: 'Исторический',
  spot: 'Спот',
  futures: 'Фьючерсы',
  buy: 'Лонг / Покупка',
  sell: 'Шорт / Продажа',
  market: 'Маркет',
  limit: 'Лимит',
  both: 'Обе стороны',
  long_only: 'Только лонг',
  short_only: 'Только шорт',
  open: 'Открыта',
  closed: 'Закрыта',
  cancelled: 'Отменена',
  filled: 'Исполнена',
  pending: 'Ожидает',
  submitted: 'Отправлено',
  partial: 'Частично',
  accepted: 'Принято',
  failed: 'Ошибка',
  completed: 'Завершено',
  success: 'Успешно',
  error: 'Ошибка',
  warning: 'Предупреждение',
  ok: 'ОК',
  yes: 'Да',
  no: 'Нет',
  enabled: 'Включен',
  disabled: 'Выключен',
  never: 'Никогда',
  unknown: 'Неизвестно',
  manual_close: 'Ручное закрытие',
  'manual-close': 'Ручное закрытие',
  stop_loss: 'Стоп-лосс',
  take_profit: 'Тейк-профит',
  tp1: 'TP1',
  tp2: 'TP2',
  tp3: 'TP3',
  breakeven: 'Безубыток',
  trailing: 'Трейлинг',
  blocked: 'Заблокирован',
  allowed: 'Разрешен',
  met: 'Достигнуто',
  'not met': 'Не достигнуто',
  'not yet': 'Пока нет',
  monday: 'Понедельник',
  tuesday: 'Вторник',
  wednesday: 'Среда',
  thursday: 'Четверг',
  friday: 'Пятница',
  saturday: 'Суббота',
  sunday: 'Воскресенье',
}

export function t(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  const raw = String(value)
  const lower = raw.toLowerCase()
  return map[raw] ?? map[lower] ?? raw.replace(/_/g, ' ')
}

export function yesNo(value: boolean | null | undefined): string {
  return value ? 'Да' : 'Нет'
}

export function onOff(value: boolean | null | undefined): string {
  return value ? 'Вкл.' : 'Выкл.'
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(date)
}

export function formatMapKey(key: string): string {
  return t(key)
}
