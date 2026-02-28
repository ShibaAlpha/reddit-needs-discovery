# Morning Routine Builder - Technical Specification

## 1. Project Overview

**Project Name:** MorningFlow  
**Bundle Identifier:** com.shibaalpha.morningflow  
**Core Functionality:** A gamified morning routine tracker that helps users build healthy morning habits with achievements, streaks, and optional social sharing.  
**Target Users:** People looking to improve their morning routines and build consistent habits.  
**iOS Version Support:** iOS 17.0+  
**Platform:** iOS (SwiftUI)

---

## 2. UI/UX Specification

### Screen Structure

| Screen | Description |
|--------|-------------|
| **HomeView** | Main dashboard showing today's routine progress, streak count, and quick actions |
| **RoutinesListView** | List of all created routines (Morning, Evening, etc.) |
| **RoutineDetailView** | Edit/view a specific routine's tasks |
| **TaskEditorView** | Add/edit individual tasks (name, duration, icon, order) |
| **StatisticsView** | Weekly/monthly completion stats, streaks, achievements |
| **AchievementsView** | Badge collection and progress |
| **SettingsView** | App preferences, data export, about |

### Navigation Structure

```
TabView (3 tabs)
├── Tab 1: Home
│   └── NavigationStack
│       ├── HomeView
│       ├── RoutineDetailView
│       └── TaskEditorView
├── Tab 2: Statistics
│   └── NavigationStack
│       └── StatisticsView
└── Tab 3: Settings
    └── NavigationStack
        └── SettingsView
```

### Visual Design

**Color Palette:**
| Role | Color | Hex |
|------|-------|-----|
| Primary | Soft Orange | `#FF8C42` |
| Secondary | Warm Yellow | `#FFD166` |
| Accent | Coral Pink | `#FF6B6B` |
| Background | Warm White | `#FFF9F5` |
| Surface | Pure White | `#FFFFFF` |
| Text Primary | Dark Gray | `#2D3436` |
| Text Secondary | Medium Gray | `#636E72` |
| Success | Mint Green | `#00B894` |
| Warning | Amber | `#FDCB6E` |

**Typography:**
| Element | Font | Size | Weight |
|---------|------|------|--------|
| Large Title | SF Pro Display | 34pt | Bold |
| Title | SF Pro Display | 28pt | Bold |
| Headline | SF Pro Text | 17pt | Semibold |
| Body | SF Pro Text | 17pt | Regular |
| Subheadline | SF Pro Text | 15pt | Regular |
| Caption | SF Pro Text | 12pt | Regular |

**Spacing System (8pt grid):**
- XS: 4pt
- S: 8pt
- M: 16pt
- L: 24pt
- XL: 32pt
- XXL: 48pt

**iOS-Specific:**
- Safe area insets respected
- Dynamic Type support
- Dark mode support (inverted colors with same hue)

### Views & Components

**Reusable Components:**

1. **TaskRow**
   - States: pending, in-progress, completed, missed
   - Shows: icon, name, duration, checkbox
   - Swipe actions: edit, delete, duplicate

2. **StreakCard**
   - Shows current streak number
   - Flame icon animation when streak > 7 days
   - Background gradient based on streak length

3. **AchievementBadge**
   - States: locked (gray), unlocked (colored), newly-unlocked (pulsing)
   - Shows: icon, title, progress bar

4. **ProgressRing**
   - Circular progress indicator for daily completion
   - Animated fill

5. **RoutineCard**
   - Preview card for routine list
   - Shows: name, task count, completion %, next scheduled time

---

## 3. Functionality Specification

### Core Features

**P0 - Must Have:**
1. **Create/Edit Routines**
   - Name, icon selection, schedule (time of day)
   - Add unlimited tasks per routine
   - Reorder tasks via drag-and-drop

2. **Daily Task Tracking**
   - Mark tasks as complete
   - Timer for timed tasks (optional)
   - Undo completion within 5 seconds

3. **Streak System**
   - Track consecutive days of completing full routine
   - Streak resets if any task missed
   - Visual streak counter with fire animation

4. **Statistics**
   - Daily/weekly/monthly completion rate
   - Best streak record
   - Most consistent days of week

**P1 - Should Have:**
5. **Achievements System**
   - 15+ achievements (see below)
   - Progress tracking per achievement
   - Unlock animations

6. **iCloud Sync**
   - SwiftData + CloudKit integration
   - Sync across devices

7. **Notifications**
   - Reminder notifications for routine time
   - Streak at risk alerts

**P2 - Nice to Have:**
8. **Social Sharing**
   - Share streak achievements to Instagram Stories
   - Shareable "I'm on a X day streak!" images

### User Flows

**Flow 1: First Launch**
1. Welcome screens (3 pages)
2. Create first routine prompt
3. Add first task
4. Set reminder time

**Flow 2: Daily Use**
1. Open app → HomeView
2. See today's routine with progress
3. Tap task → Mark complete
4. Repeat until all done
5. See celebration animation

**Flow 3: Routine Management**
1. Tap "Edit Routine" on HomeView
2. Add/remove/reorder tasks
3. Change routine schedule
4. Save

### Data Model (SwiftData)

```swift
@Model
class Routine {
    var id: UUID
    var name: String
    var icon: String // SF Symbol name
    var scheduledTime: Date // Time only
    var createdAt: Date
    var tasks: [TaskItem]
    var isArchived: Bool
}

@Model
class TaskItem {
    var id: UUID
    var name: String
    var icon: String
    var durationMinutes: Int?
    var orderIndex: Int
    var isCompleted: Bool
    var completedAt: Date?
    var routine: Routine?
}

@Model
class DailyRecord {
    var id: UUID
    var date: Date // Day only
    var routine: Routine?
    var completionRate: Double // 0.0 - 1.0
    var tasksCompleted: Int
    var totalTasks: Int
}

@Model
class Achievement {
    var id: String // unique key
    var isUnlocked: Bool
    var unlockedAt: Date?
    var progress: Double // 0.0 - 1.0
}
```

### Achievements List

| ID | Name | Description | Criteria |
|----|------|-------------|----------|
| first_step | First Step | Complete your first task | Complete 1 task |
| routine_starter | Routine Starter | Complete a full routine | 100% completion in a day |
| week_warrior | Week Warrior | 7 day streak | 7 consecutive days |
| month_master | Month Master | 30 day streak | 30 consecutive days |
| early_bird | Early Bird | Complete routine before 7am | Complete before 7am |
| night_owl | Night Owl | Complete routine after 10pm | Complete after 10pm |
| perfectionist | Perfectionist | 100% weekly completion | 7/7 days |
| task_master | Task Master | Complete 100 tasks | Total 100 tasks |
| diversity | Diversity | Create 3+ routines | 3 routines |
| consistent | Consistent | Same time for 7 days | Same time 7 days |
| first_achievement | Achievement Unlocked | First achievement | Unlock any achievement |
| collector | Collector | Unlock 10 achievements | 10 achievements |
| dedicated | Dedicated | Use app for 30 days | 30 days active |
| sharer | Social Butterfly | Share achievement | First share |

### Error Handling

- Network errors: Show banner, use cached data
- iCloud sync conflicts: Last-write-wins with user notification
- Invalid input: Inline validation messages (red text below field)
- Empty states: Friendly illustrations with action buttons

---

## 4. Technical Specification

### Architecture

**Pattern:** MVVM with SwiftUI

```
Views/
├── Home/
├── Routines/
├── Statistics/
├── Settings/
└── Components/

ViewModels/
├── HomeViewModel.swift
├── RoutineViewModel.swift
├── StatisticsViewModel.swift
└── AchievementViewModel.swift

Models/
├── Routine.swift
├── TaskItem.swift
├── DailyRecord.swift
└── Achievement.swift

Services/
├── NotificationService.swift
├── CloudKitService.swift
└── ShareService.swift
```

### Dependencies (Swift Package Manager)

| Package | Version | Purpose |
|---------|---------|---------|
| None required | - | Using native SwiftUI + SwiftData |

### UI Framework

- **SwiftUI** for all views
- **SwiftData** for persistence (iOS 17+)
- **CloudKit** via SwiftData for sync
- **UserNotifications** for reminders

### Asset Requirements

**SF Symbols Used:**
- checkmark.circle.fill
- flame.fill
- star.fill
- sun.max.fill
- moon.fill
- bed.double.fill
- figure.walk
- book.fill
- cup.and.saucer.fill
- dumbbell.fill
- heart.fill
- bolt.fill
- leaf.fill

**Custom Assets:**
- App Icon (1024x1024)
- Achievement badge icons (optional - can use SF Symbols)
- Empty state illustrations (optional)

### CloudKit Configuration

- Container: `iCloud.com.shibaalpha.morningflow`
- Enable CloudKit in Xcode
- SwiftData with CloudKit integration

---

## 5. Implementation Plan

### Phase 1: Core (Week 1-2)
- [ ] Project setup with Xcode
- [ ] SwiftData models
- [ ] HomeView with routine display
- [ ] Task completion flow
- [ ] Basic streak tracking

### Phase 2: Management (Week 3)
- [ ] Create/edit routines
- [ ] Create/edit tasks
- [ ] Routine scheduling
- [ ] Delete/archive routines

### Phase 3: Engagement (Week 4)
- [ ] Statistics view
- [ ] Achievements system
- [ ] iCloud sync

### Phase 4: Polish (Week 5)
- [ ] Notifications
- [ ] Social sharing
- [ ] Dark mode
- [ ] App store assets

---

## 6. File Structure

```
MorningFlow/
├── App/
│   └── MorningFlowApp.swift
├── Views/
│   ├── Home/
│   │   ├── HomeView.swift
│   │   └── HomeViewModel.swift
│   ├── Routines/
│   │   ├── RoutinesListView.swift
│   │   ├── RoutineDetailView.swift
│   │   ├── RoutineEditorView.swift
│   │   └── TaskEditorView.swift
│   ├── Statistics/
│   │   ├── StatisticsView.swift
│   │   └── StatisticsViewModel.swift
│   ├── Settings/
│   │   └── SettingsView.swift
│   └── Components/
│       ├── TaskRow.swift
│       ├── StreakCard.swift
│       ├── AchievementBadge.swift
│       ├── ProgressRing.swift
│       └── RoutineCard.swift
├── Models/
│   ├── Routine.swift
│   ├── TaskItem.swift
│   ├── DailyRecord.swift
│   └── Achievement.swift
├── Services/
│   ├── NotificationService.swift
│   └── ShareService.swift
├── Extensions/
│   ├── Color+Theme.swift
│   └── Date+Extensions.swift
└── Resources/
    └── Assets.xcassets/
```

---

*Generated: 2026-02-28*
