"use client"

import * as React from "react"
import { ChevronDown, ChevronLeft, ChevronRight } from "lucide-react"
import { DayPicker, getDefaultClassNames } from "react-day-picker"
import { ru } from "date-fns/locale"

import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

export type CalendarProps = React.ComponentProps<typeof DayPicker>

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}: CalendarProps) {
  const defaultClassNames = getDefaultClassNames()

  return (
    <DayPicker
      locale={ru}
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        root: cn("w-fit", defaultClassNames.root),
        months: cn(
          "flex flex-col sm:flex-row gap-4 relative",
          defaultClassNames.months
        ),
        month: cn("flex flex-col w-full gap-4", defaultClassNames.month),
        month_caption: cn(
          "flex h-9 w-full items-center justify-center px-9",
          defaultClassNames.month_caption
        ),
        caption_label: cn(
          "inline-flex w-full items-center justify-between gap-1.5 whitespace-nowrap text-sm font-semibold leading-none select-none",
          defaultClassNames.caption_label
        ),
        dropdowns: cn(
          "flex items-center justify-center gap-1.5",
          defaultClassNames.dropdowns
        ),
        dropdown: cn(
          "absolute inset-0 z-10 w-full cursor-pointer opacity-0",
          defaultClassNames.dropdown
        ),
        dropdown_root: cn(
          "relative inline-flex h-9 items-center rounded-lg border border-input/80 bg-background px-2.5 text-sm font-medium shadow-sm transition-colors focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/30 has-[.rdp-months_dropdown]:min-w-[8.5rem] has-[.rdp-years_dropdown]:min-w-[6rem]",
          defaultClassNames.dropdown_root
        ),
        months_dropdown: cn(
          "cursor-pointer",
          defaultClassNames.months_dropdown
        ),
        years_dropdown: cn(
          "cursor-pointer",
          defaultClassNames.years_dropdown
        ),
        nav: cn(
          "absolute inset-x-0 top-0 flex h-9 items-center justify-between",
          defaultClassNames.nav
        ),
        button_previous: cn(
          buttonVariants({ variant: "outline" }),
          "h-7 w-7 rounded-lg bg-background p-0 text-muted-foreground opacity-80 hover:bg-accent hover:text-foreground hover:opacity-100",
          defaultClassNames.button_previous
        ),
        button_next: cn(
          buttonVariants({ variant: "outline" }),
          "h-7 w-7 rounded-lg bg-background p-0 text-muted-foreground opacity-80 hover:bg-accent hover:text-foreground hover:opacity-100",
          defaultClassNames.button_next
        ),
        weekdays: cn("flex", defaultClassNames.weekdays),
        weekday: cn(
          "text-muted-foreground rounded-md w-8 font-normal text-[0.8rem] select-none",
          defaultClassNames.weekday
        ),
        week: cn("flex w-full mt-2", defaultClassNames.week),
        day: cn(
          "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([aria-selected])]:bg-accent [&:has([aria-selected])]:rounded-md",
          defaultClassNames.day
        ),
        day_button: cn(
          buttonVariants({ variant: "ghost" }),
          "h-8 w-8 p-0 font-normal aria-selected:opacity-100",
          defaultClassNames.day_button
        ),
        selected:
          "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground rounded-md",
        today: cn(
          "bg-accent text-accent-foreground rounded-md",
          defaultClassNames.today
        ),
        outside: cn(
          "text-muted-foreground aria-selected:bg-accent/50 aria-selected:text-muted-foreground",
          defaultClassNames.outside
        ),
        disabled: cn(
          "text-muted-foreground opacity-50",
          defaultClassNames.disabled
        ),
        hidden: cn("invisible", defaultClassNames.hidden),
        range_start: cn("rounded-l-md bg-accent", defaultClassNames.range_start),
        range_middle: cn("rounded-none", defaultClassNames.range_middle),
        range_end: cn("rounded-r-md bg-accent", defaultClassNames.range_end),
        ...classNames,
      }}
      components={{
        Chevron: ({ orientation, ...chevronProps }) => {
          if (orientation === "left") {
            return <ChevronLeft className="h-4 w-4" {...chevronProps} />
          }
          if (orientation === "down") {
            return <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" {...chevronProps} />
          }
          return <ChevronRight className="h-4 w-4" {...chevronProps} />
        },
      }}
      {...props}
    />
  )
}
Calendar.displayName = "Calendar"

export { Calendar }
