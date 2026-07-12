import * as React from 'react';
import { Moon, Sun } from 'lucide-react';

import { Button } from '@/components/ui/button';

type Theme = 'theme-light' | 'dark';

const storageKey = 'theme';

function isTheme(value: string | null): value is Theme {
  return value === 'theme-light' || value === 'dark';
}

function getInitialTheme(): Theme {
  if (typeof document === 'undefined') return 'theme-light';

  const storedTheme = localStorage.getItem(storageKey);
  if (isTheme(storedTheme)) return storedTheme;

  return document.documentElement.classList.contains('dark')
    ? 'dark'
    : 'theme-light';
}

function applyTheme(theme: Theme) {
  document.documentElement.classList[theme === 'dark' ? 'add' : 'remove'](
    'dark',
  );
}

export function ThemeToggle() {
  const [theme, setThemeState] = React.useState<Theme>(getInitialTheme);

  React.useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  function toggleTheme() {
    const nextTheme = theme === 'dark' ? 'theme-light' : 'dark';
    setThemeState(nextTheme);
    localStorage.setItem(storageKey, nextTheme);
  }

  return (
    <Button
      variant="secondary"
      size="icon"
      type="button"
      onClick={toggleTheme}
      aria-pressed={theme === 'dark'}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
    >
      <Sun className="scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
      <Moon className="absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
