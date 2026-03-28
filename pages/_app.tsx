import type { AppProps } from 'next/app';
import Head from 'next/head';
import LockScreen from '@/components/LockScreen';
import { ThemeProvider } from '@/lib/ThemeContext';
import { SyncProvider } from '@/lib/SyncContext';
import { TabProvider } from '@/lib/TabContext';
import { TagProvider } from '@/lib/TagContext';
import { AnnotationProvider } from '@/lib/AnnotationContext';
import '@/styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover" />
      </Head>
      <LockScreen>
        <ThemeProvider>
          <SyncProvider>
            <AnnotationProvider>
              <TagProvider>
                <TabProvider>
                  <Component {...pageProps} />
                </TabProvider>
              </TagProvider>
            </AnnotationProvider>
          </SyncProvider>
        </ThemeProvider>
      </LockScreen>
    </>
  );
}
