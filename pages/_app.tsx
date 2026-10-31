import type { AppProps } from 'next/app';
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import LockScreen from '@/components/LockScreen';
import { ThemeProvider } from '@/lib/ThemeContext';
import { SyncProvider } from '@/lib/SyncContext';
import { TabProvider } from '@/lib/TabContext';
import { TagProvider } from '@/lib/TagContext';
import { AnnotationProvider } from '@/lib/AnnotationContext';
import { DocStoreProvider } from '@/lib/DocStoreContext';
import '@/styles/globals.css';

function useScreenshotMode() {
  const router = useRouter();
  useEffect(() => {
    if (router.query.screenshot === '1') {
      document.documentElement.classList.add('screenshot-mode');
    }
  }, [router.query.screenshot]);
}

export default function App({ Component, pageProps }: AppProps) {
  useScreenshotMode();
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
                  <DocStoreProvider>
                    <Component {...pageProps} />
                  </DocStoreProvider>
                </TabProvider>
              </TagProvider>
            </AnnotationProvider>
          </SyncProvider>
        </ThemeProvider>
      </LockScreen>
    </>
  );
}