import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: ["class"],
    content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	extend: {
  		fontFamily: {
  			heading: ['var(--font-heading)', 'system-ui', 'sans-serif'],
  			body: ['var(--font-body)', 'system-ui', 'sans-serif'],
  			mono: ['var(--font-geist-mono)', 'ui-monospace', 'monospace'],
  		},
  		fontSize: {
  			'2xs': ['0.6875rem', { lineHeight: '1rem' }],
  		},
  		colors: {
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			// Semantic: task statuses
  			status: {
  				new: {
  					bg: 'hsl(var(--status-new-bg))',
  					fg: 'hsl(var(--status-new-fg))',
  					ring: 'hsl(var(--status-new-ring))',
  				},
  				progress: {
  					bg: 'hsl(var(--status-progress-bg))',
  					fg: 'hsl(var(--status-progress-fg))',
  					ring: 'hsl(var(--status-progress-ring))',
  				},
  				review: {
  					bg: 'hsl(var(--status-review-bg))',
  					fg: 'hsl(var(--status-review-fg))',
  					ring: 'hsl(var(--status-review-ring))',
  				},
  				done: {
  					bg: 'hsl(var(--status-done-bg))',
  					fg: 'hsl(var(--status-done-fg))',
  					ring: 'hsl(var(--status-done-ring))',
  				},
  				cancelled: {
  					bg: 'hsl(var(--status-cancelled-bg))',
  					fg: 'hsl(var(--status-cancelled-fg))',
  					ring: 'hsl(var(--status-cancelled-ring))',
  				},
  			},
  			// Semantic: priorities
  			priority: {
  				urgent: {
  					bg: 'hsl(var(--priority-urgent-bg))',
  					fg: 'hsl(var(--priority-urgent-fg))',
  					dot: 'hsl(var(--priority-urgent-dot))',
  				},
  				high: {
  					bg: 'hsl(var(--priority-high-bg))',
  					fg: 'hsl(var(--priority-high-fg))',
  					dot: 'hsl(var(--priority-high-dot))',
  				},
  				medium: {
  					bg: 'hsl(var(--priority-medium-bg))',
  					fg: 'hsl(var(--priority-medium-fg))',
  					dot: 'hsl(var(--priority-medium-dot))',
  				},
  				low: {
  					bg: 'hsl(var(--priority-low-bg))',
  					fg: 'hsl(var(--priority-low-fg))',
  					dot: 'hsl(var(--priority-low-dot))',
  				},
  			},
  			// Semantic: roles
  			role: {
  				moderator: {
  					bg: 'hsl(var(--role-moderator-bg))',
  					fg: 'hsl(var(--role-moderator-fg))',
  					ring: 'hsl(var(--role-moderator-ring))',
  				},
  				member: {
  					bg: 'hsl(var(--role-member-bg))',
  					fg: 'hsl(var(--role-member-fg))',
  					ring: 'hsl(var(--role-member-ring))',
  				},
  			},
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
