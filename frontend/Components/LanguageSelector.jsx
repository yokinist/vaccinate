// @flow
import * as React from 'react';
import { useTranslation } from 'react-i18next';

import locales from '../Constants/Locales';

export default function LanguageSelector(): React.Node {
  const { i18n } = useTranslation();

  return (
    <div className="dropdown d-none d-xl-block">
      <button
        id="languageDropdown"
        className="btn btn-outline-secondary btn-sm dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        aria-expanded="false"
        aria-label="Select a language"
      >
        <i className="bi bi-globe" />
      </button>
      <ul
        className="dropdown-menu dropdown-menu-end"
        aria-labelledby="languageDropdown"
      >
        {
          Object.keys(locales).map((key) => (
            <li
              key={`lang_${key}`}
            >
              <button
                className="dropdown-item"
                type="button"
                aria-label={locales[key].text}
                onClick={() => { i18n.changeLanguage(locales[key].locale); }}
              >
                {locales[key].text}
              </button>
            </li>
          ))
        }
      </ul>
    </div>
  );
}
