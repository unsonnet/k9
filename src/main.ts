(window as any).JXLDecoderConfig = {
  decoderUrl: '/k9/assets/jxl/jxl_dec.js',
  debug: true,
};

import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

bootstrapApplication(App, appConfig).catch((err) => console.error(err));
