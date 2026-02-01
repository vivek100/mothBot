'use client';

import { useState } from 'react';

import { ThemeProvider } from '@pipecat-ai/voice-ui-kit';

import type { PipecatBaseChildProps } from '@pipecat-ai/voice-ui-kit';
import {
  FullScreenContainer,
  PipecatAppBase,
  SpinLoader,
} from '@pipecat-ai/voice-ui-kit';

import { App } from './components/App';
import {
  AVAILABLE_TRANSPORTS,
  DEFAULT_TRANSPORT,
  TRANSPORT_CONFIG,
} from '../config';
import type { TransportType } from '../config';

export default function Home() {
  const [transportType, setTransportType] =
    useState<TransportType>(DEFAULT_TRANSPORT);

  const connectParams = TRANSPORT_CONFIG[transportType];

  return (
    <ThemeProvider defaultTheme="terminal" disableStorage>
      <FullScreenContainer>
        <PipecatAppBase
          connectParams={connectParams}
          transportType={transportType}>
          {({
            client,
            handleConnect,
            handleDisconnect,
            error,
          }: PipecatBaseChildProps) =>
            !client ? (
              <SpinLoader />
            ) : (
              <App
                client={client}
                handleConnect={handleConnect}
                handleDisconnect={handleDisconnect}
                transportType={transportType}
                onTransportChange={setTransportType}
                availableTransports={AVAILABLE_TRANSPORTS}
                error={error}
              />
            )
          }
        </PipecatAppBase>
      </FullScreenContainer>
    </ThemeProvider>
  );
}
