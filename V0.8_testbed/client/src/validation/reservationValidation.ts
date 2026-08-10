// Shared client-side validation for the reservation form fields
// (docs/P002-frontend-spec.md 3.3節, also used as-is by 3.4節's edit form -
// "バリデーションルールはS03と同一"). Used by both
// client/src/pages/ReservationCreatePage.tsx (S03) and
// client/src/pages/ReservationDetailPage.tsx (S04, U004-T3), per U004-T3's
// own 実装してはいけないこと: rather than duplicating this logic in S04 or
// editing S03's internals freely, it is factored out here and both screens
// reference it.

export const TITLE_MAX_LENGTH = 100
export const NOTES_MAX_LENGTH = 500
// CR-001 (docs/P901-cr-direction/CR-001.md, U003-T8): オンライン会議URL。
export const MEETING_URL_MAX_LENGTH = 500

export interface ReservationFormValues {
  roomId: string
  date: string
  startTime: string
  endTime: string
  title: string
  attendeeCount: string
  notes: string
  meetingUrl: string
}

export interface ReservationFormErrors {
  roomId?: string
  date?: string
  startTime?: string
  endTime?: string
  title?: string
  attendeeCount?: string
  notes?: string
  meetingUrl?: string
}

export function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

export function validateReservationForm(
  values: ReservationFormValues,
  roomCapacity: number | undefined,
): ReservationFormErrors {
  const errors: ReservationFormErrors = {}

  if (!values.roomId) {
    errors.roomId = '会議室を選択してください'
  }

  if (!values.date) {
    errors.date = '日付を選択してください'
  } else if (values.date < todayIsoDate()) {
    errors.date = '過去の日付は指定できません'
  }

  if (!values.startTime) {
    errors.startTime = '開始時刻を入力してください'
  }

  if (!values.endTime || values.endTime <= values.startTime) {
    errors.endTime = '終了時刻は開始時刻より後にしてください'
  }

  if (!values.title.trim()) {
    errors.title = '件名を入力してください'
  } else if (values.title.length > TITLE_MAX_LENGTH) {
    errors.title = '件名は100文字以内で入力してください'
  }

  if (values.attendeeCount.trim() !== '') {
    const attendeeCount = Number(values.attendeeCount)
    if (!Number.isInteger(attendeeCount) || attendeeCount < 1) {
      errors.attendeeCount = '参加予定人数は1以上の整数で入力してください'
    } else if (roomCapacity !== undefined && attendeeCount > roomCapacity) {
      errors.attendeeCount = `選択した会議室の収容人数(${roomCapacity}名)を超えています`
    }
  }

  if (values.notes.length > NOTES_MAX_LENGTH) {
    errors.notes = '備考は500文字以内で入力してください'
  }

  // CR-001 (docs/P002-frontend-spec.md 3.3節): 空欄は許容する(必須項目にしない)。
  if (values.meetingUrl.trim() !== '') {
    if (!values.meetingUrl.startsWith('http://') && !values.meetingUrl.startsWith('https://')) {
      errors.meetingUrl = 'オンライン会議URLは http:// または https:// で始めてください'
    } else if (values.meetingUrl.length > MEETING_URL_MAX_LENGTH) {
      errors.meetingUrl = 'オンライン会議URLは500文字以内で入力してください'
    }
  }

  return errors
}
