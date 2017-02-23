import os
import logging
import uuid
import shutil
import subprocess

from collections import deque
from datetime import datetime

from .exceptions import FFmpegProcessException, FFmpegBinaryNotFound, FFmpegInputNotFoundException, \
    FFmpegOutputAlreadyExistsException


logging.info('FFmpeg is a trademark of Fabrice Bellard <http://www.bellard.org/>, originator of the FFmpeg project.')


class FFmpegBaseCommand:

    DEFAULT_GENERAL_ARGS = ['-hide_banner', '-n', '-nostdin', '-loglevel', 'warning', '-stats']

    def __init__(self, bin_path: str, tmp_dir: str):
        bin_path = os.path.abspath(bin_path)
        if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
            msg = 'FFmpeg binary not found: "{}"'.format(bin_path)
            logging.critical(msg)
            raise FFmpegBinaryNotFound(msg)
        self._bin_path = bin_path
        self._tmp_dir = os.path.abspath(tmp_dir)

    def _success_callback(self, output_mapping: list, simulate) -> None:
        logging.info('Moving files from temporary directory...')
        for tmp_path, out_path in output_mapping:
            logging.debug('Temporary file: "{}"; output file: "{}"'.format(tmp_path, out_path))
            if os.path.exists(out_path):
                logging.warning('Output file "{}" already exists'.format(out_path))
                head, tail = os.path.split(out_path)
                name, ext = os.path.splitext(tail)
                out_path = os.path.join(
                    head,
                    '{}.{}{}'.format(
                        name,
                        os.path.splitext(os.path.split(tmp_path)[1])[0][0:8],
                        ext
                    )
                )
                logging.warning('New output file name: "{}"'.format(out_path))
            if not simulate:
                shutil.move(tmp_path, out_path)
        logging.info('Done')

    def _progress_callback(self, frame: int) -> None:
        logging.debug('Processed {} frames'.format(frame))

    def _error_callback(self, return_code: int, proc_log: deque, proc_exception: Exception, tmp_paths: list) -> None:
        logging.info('Removing temporary files...')
        for t in tmp_paths:
            if os.path.exists(t):
                logging.debug('Found: "{}" - removing...'.format(t))
                os.remove(t)
        raise FFmpegProcessException(
            'FFmpeg exit code {}.\r\nLast output: {}\r\nRaised exception: {}'.format(
                return_code, ' '.join(proc_log), proc_exception
            )
        )

    def exec(self, inputs: list, outputs: list, simulate: bool, general_args: list=None):
        if general_args is None:
            general_args = self.__class__.DEFAULT_GENERAL_ARGS
        logging.debug('Building FFmpeg command...')
        args = [self._bin_path]
        logging.debug('General args: {}'.format(general_args))
        args.extend(general_args)

        logging.debug('Appending inputs...')
        for i in inputs:
            in_args, in_url = i
            if not os.path.isfile(in_url):
                msg = 'Input file not found: "{}"'.format(in_url)
                logging.error(msg)
                raise FFmpegInputNotFoundException(msg)
            in_args.append('-i')
            in_args.append(in_url)
            logging.debug('Extending args with {}'.format(in_args))
            args.extend(in_args)

        logging.debug('Appending outputs...')
        output_mapping = []
        for o in outputs:
            out_args, out_path = o
            if os.path.exists(out_path):
                msg = 'Output file "{}" already exists'.format(out_path)
                logging.error(msg)
                raise FFmpegOutputAlreadyExistsException(msg)
            out_ext = os.path.splitext(os.path.split(out_path)[1])[1]
            tmp_path = os.path.join(self._tmp_dir, '{}{}'.format(str(uuid.uuid4()), out_ext))
            output_mapping.append((tmp_path, out_path))
            out_args.append(tmp_path)
            logging.debug('Extending args with {}'.format(out_args))
            args.extend(out_args)
        logging.debug('Output mapping (tmp_path, out_path): {}'.format(output_mapping))

        logging.info('Starting FFmpeg...')
        logging.debug(' '.join(args))
        if simulate:
            self._success_callback(output_mapping, simulate)
            return

        proc_log = deque(maxlen=5)
        proc_exception = None
        proc = subprocess.Popen(args, stderr=subprocess.PIPE, universal_newlines=True)
        proc_start_time = datetime.now()
        logging.info('FFmpeg process started at {}'.format(proc_start_time))

        ignoring_progress = False
        try:
            for line in proc.stderr:
                proc_log.append(line)
                if not ignoring_progress and line.startswith('frame='):
                    p = line.find('fps=')
                    try:
                        frame = int(line[6:p].strip())
                    except ValueError:
                        logging.warning(line)
                        logging.warning('Unable to determine conversion progress - ignoring it')
                        ignoring_progress = True
                    else:
                        self._progress_callback(frame)
        except FFmpegProcessException as e:
            proc.terminate()
            proc_exception = e
        except Exception as e:
            proc.terminate()
            logging.error(str(e))
        finally:
            proc.wait()
            proc_end_time = datetime.now()
            logging.info('FFmpeg process finished at {}. Elapsed time: {}'.format(
                proc_end_time, proc_end_time - proc_start_time)
            )
            return_code = proc.returncode
            if return_code != 0:
                self._error_callback(
                    return_code, proc_log, proc_exception,
                    [t for t, o in output_mapping]
                )
            else:
                self._success_callback(output_mapping, simulate)
