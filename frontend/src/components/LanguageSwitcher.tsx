import React, { memo, useState, useRef, useEffect } from 'react';
import useTranslation from '../hooks/useTranslation';
import { MdCheck, MdExpandMore } from 'react-icons/md';

/**
 * Premium language switcher — compact dropdown with flag + name.
 * Renders as a button that opens a floating panel.
 */
const LanguageSwitcher: React.FC = memo(() => {
  const { language, setLanguage, availableLanguages } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selected = availableLanguages.find((l: any) => l.code === language) || availableLanguages[0];

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKey);
      return () => document.removeEventListener('keydown', handleKey);
    }
  }, [isOpen]);

  return (
    <div ref={dropdownRef} className="relative inline-block">
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-semibold
                   bg-white text-slate-700 border border-slate-200 hover:border-brand-accent/30
                   hover:shadow-sm transition-all duration-200 active:scale-95"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        id="language-switcher-trigger"
      >
        <span className="text-lg leading-none">{selected.flag}</span>
        <span className="hidden sm:inline">{selected.nativeName}</span>
        <MdExpandMore
          className={`text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div
          className="absolute right-0 top-full mt-2 z-100 min-w-[200px] bg-white rounded-2xl
                     shadow-xl shadow-black/10 border border-slate-100 py-2 overflow-hidden
                     animate-in fade-in slide-in-from-top-2 duration-200"
          role="listbox"
          aria-labelledby="language-switcher-trigger"
        >
          {availableLanguages.map((lang: any) => {
            const isSelected = language === lang.code;
            return (
              <button
                key={lang.code}
                role="option"
                aria-selected={isSelected}
                onClick={() => {
                  setLanguage(lang.code);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm
                           transition-colors duration-150
                           ${isSelected
                    ? 'bg-brand-accent/10 text-brand-accent font-bold'
                    : 'text-slate-600 hover:bg-slate-50'
                  }`}
              >
                <span className="text-lg leading-none">{lang.flag}</span>
                <span className="flex-1">{lang.nativeName}</span>
                {isSelected && <MdCheck className="text-brand-accent text-lg" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
});

LanguageSwitcher.displayName = 'LanguageSwitcher';

export default LanguageSwitcher;
