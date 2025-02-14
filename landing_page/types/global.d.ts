interface Window {
    institutionSelector: (
      institutions: any[],
      elementId: string,
      config: {
        redirectUrl: string;
        logoUrl: string;
        text: string;
        countryFilter: boolean;
        styles: {
          fontFamily: string;
          fontSize: string;
          backgroundColor: string;
          textColor: string;
          headingColor: string;
          linkColor: string;
          modalTextColor: string;
          modalBackgroundColor: string;
        };
      }
    ) => void;
  }